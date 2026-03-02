#!/bin/bash
set -e

# ============================================================
# PIM Azure リソースロール一括アクティブ化スクリプト
# ============================================================
# 事前に以下でログインしておくこと:
#   az login --tenant <tenant-id> --allow-no-subscriptions
# ============================================================

# --- 共通設定 ---
USER_ID="<your-user-object-id>"          # az ad signed-in-user show --query id -o tsv
JUSTIFICATION="${1:-日常運用作業}"         # 第1引数で理由を渡せる。省略時はデフォルト値
API_VERSION="2020-10-01"

# --- アクセストークンを取得 ---
echo "🔑 アクセストークンを取得中..."
ACCESS_TOKEN=$(az account get-access-token --resource https://management.azure.com --query accessToken -o tsv 2>&1) || {
  echo "❌ トークン取得に失敗しました。az login --tenant <tenant-id> --allow-no-subscriptions を実行してください。"
  echo "エラー: ${ACCESS_TOKEN}"
  exit 1
}
echo "✅ トークン取得成功"
echo ""

# --- ロール定義（5つ分） ---
#   SCOPE        : properties.scope
#   ROLE_DEF_ID  : properties.roleDefinitionId
#   ELIGIBILITY_ID : name
#   DURATION     : ロールごとの上限値（PT1H, PT4H, PT8H など）

ROLES=(
  # "スコープ|ロール定義ID|eligibilityスケジュールID|わかりやすい名前|有効期間"
  "<scope-1>|<role-definition-id-1>|<eligibility-schedule-id-1>|Role1の名前|PT8H"
  "<scope-2>|<role-definition-id-2>|<eligibility-schedule-id-2>|Role2の名前|PT4H"
  "<scope-3>|<role-definition-id-3>|<eligibility-schedule-id-3>|Role3の名前|PT1H"
  "<scope-4>|<role-definition-id-4>|<eligibility-schedule-id-4>|Role4の名前|PT8H"
  "<scope-5>|<role-definition-id-5>|<eligibility-schedule-id-5>|Role5の名前|PT4H"
)

# ============================================================
# アクティブ化の実行
# ============================================================

echo "=========================================="
echo " PIM ロール一括アクティブ化"
echo " 理由: ${JUSTIFICATION}"
echo "=========================================="
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

for ROLE in "${ROLES[@]}"; do
  IFS='|' read -r SCOPE ROLE_DEF_ID ELIGIBILITY_ID ROLE_NAME DURATION <<< "${ROLE}"
  REQUEST_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

  echo "▶ アクティブ化中: ${ROLE_NAME}"
  echo "  スコープ: ${SCOPE}"
  echo "  有効期間: ${DURATION}"

  BODY=$(cat <<EOF
{
  "properties": {
    "principalId": "${USER_ID}",
    "roleDefinitionId": "${ROLE_DEF_ID}",
    "requestType": "SelfActivate",
    "linkedRoleEligibilityScheduleId": "${ELIGIBILITY_ID}",
    "justification": "${JUSTIFICATION}",
    "scheduleInfo": {
      "expiration": {
        "type": "AfterDuration",
        "duration": "${DURATION}"
      }
    }
  }
}
EOF
  )

  URL="https://management.azure.com${SCOPE}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/${REQUEST_ID}?api-version=${API_VERSION}"

  HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${URL}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${BODY}" 2>&1)

  HTTP_CODE=$(echo "${HTTP_RESPONSE}" | tail -1)
  RESPONSE_BODY=$(echo "${HTTP_RESPONSE}" | sed '$d')

  if [[ "${HTTP_CODE}" =~ ^2 ]]; then
    echo "  ✅ 成功 (HTTP ${HTTP_CODE})"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    echo "  ❌ 失敗 (HTTP ${HTTP_CODE})"
    echo "  エラー: ${RESPONSE_BODY}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi

  echo ""
done

# ============================================================
# 結果サマリー
# ============================================================
echo "=========================================="
echo " 完了: ✅ ${SUCCESS_COUNT} 成功 / ❌ ${FAIL_COUNT} 失敗"
echo "=========================================="