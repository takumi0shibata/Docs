#!/bin/bash
set -e

# ============================================================
# PIM Azure リソースロール一括アクティブ化スクリプト
# ============================================================

# --- 共通設定 ---
USER_ID="<your-user-object-id>"          # az ad signed-in-user show --query id -o tsv
DURATION="PT8H"                           # アクティブ化の有効期間（PT1H, PT4H, PT8H など）
JUSTIFICATION="${1:-日常運用作業}"         # 第1引数で理由を渡せる。省略時はデフォルト値
API_VERSION="2020-10-01"

# --- ロール定義（5つ分） ---
# az rest --method GET \
#   --url "https://management.azure.com/providers/Microsoft.Authorization/roleEligibilityScheduleInstances?api-version=2020-10-01&\$filter=asTarget()" \
#   --query "value[].{name:name, scope:properties.scope, roleName:properties.expandedProperties.roleDefinition.displayName, roleDefId:properties.roleDefinitionId}" \
#   -o table
# 上記で取得したテーブルの値をここに埋める
#   SCOPE        : properties.scope
#   ROLE_DEF_ID  : properties.roleDefinitionId
#   ELIGIBILITY_ID : name

ROLES=(
  # "スコープ|ロール定義ID|eligibilityスケジュールID|わかりやすい名前"
  "<scope-1>|<role-definition-id-1>|<eligibility-schedule-id-1>|Role1の名前"
  "<scope-2>|<role-definition-id-2>|<eligibility-schedule-id-2>|Role2の名前"
  "<scope-3>|<role-definition-id-3>|<eligibility-schedule-id-3>|Role3の名前"
  "<scope-4>|<role-definition-id-4>|<eligibility-schedule-id-4>|Role4の名前"
  "<scope-5>|<role-definition-id-5>|<eligibility-schedule-id-5>|Role5の名前"
)

# ============================================================
# アクティブ化の実行
# ============================================================

echo "=========================================="
echo " PIM ロール一括アクティブ化"
echo " 有効期間: ${DURATION}"
echo " 理由: ${JUSTIFICATION}"
echo "=========================================="
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

for ROLE in "${ROLES[@]}"; do
  IFS='|' read -r SCOPE ROLE_DEF_ID ELIGIBILITY_ID ROLE_NAME <<< "${ROLE}"
  REQUEST_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

  echo "▶ アクティブ化中: ${ROLE_NAME}"
  echo "  スコープ: ${SCOPE}"

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

  HTTP_RESPONSE=$(az rest --method PUT \
    --url "https://management.azure.com${SCOPE}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/${REQUEST_ID}?api-version=${API_VERSION}" \
    --body "${BODY}" 2>&1) && {
      echo "  ✅ 成功"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    } || {
      echo "  ❌ 失敗"
      echo "  エラー: ${HTTP_RESPONSE}"
      FAIL_COUNT=$((FAIL_COUNT + 1))
    }

  echo ""
done

# ============================================================
# 結果サマリー
# ============================================================
echo "=========================================="
echo " 完了: ✅ ${SUCCESS_COUNT} 成功 / ❌ ${FAIL_COUNT} 失敗"
echo "=========================================="
