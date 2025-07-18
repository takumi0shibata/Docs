import json
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from collections import defaultdict, Counter
import numpy as np
import colorsys

class SustainabilityGraphIntegrator:
    def __init__(self):
        self.integrated_graph = nx.DiGraph()
        self.cluster_data = defaultdict(lambda: {
            'type': '',
            'texts': [],
            'companies': set(),
            'count': 0
        })
        self.edge_weights = defaultdict(int)
        self.relation_types = {
            'addresses_risk': {'color': '#FF6B6B', 'description': 'リスクへの対応'},
            'addresses_opportunity': {'color': '#4ECDC4', 'description': '機会への対応'},
            'leads_to': {'color': '#45B7D1', 'description': '戦略から目標/実績へ'},
            'evaluated_by': {'color': '#96CEB4', 'description': '目標の実績評価'}
        }
    
    def load_company_data(self, company_data_list):
        """
        複数企業のデータを読み込んで統合グラフを構築
        
        Args:
            company_data_list: 各企業のJSONデータのリスト
        """
        for company_idx, company_data in enumerate(company_data_list):
            company_name = f"Company_{company_idx + 1}"
            
            # ノードデータの統合
            for node in company_data.get('nodes', []):
                cluster_id = node['cluster']
                node_type = node['type']
                text = node['text']
                
                # typeとclusterの組み合わせで一意なクラスタIDを作成
                unique_cluster_id = f"{node_type}_{cluster_id}"
                
                # クラスタ情報の更新
                if unique_cluster_id not in self.cluster_data:
                    self.cluster_data[unique_cluster_id]['type'] = node_type
                
                self.cluster_data[unique_cluster_id]['texts'].append({
                    'company': company_name,
                    'text': text,
                    'original_id': node['id']
                })
                self.cluster_data[unique_cluster_id]['companies'].add(company_name)
                self.cluster_data[unique_cluster_id]['count'] += 1
            
            # エッジデータの統合
            for edge in company_data.get('edges', []):
                # 元のノードIDからクラスタIDを取得
                source_cluster = None
                target_cluster = None
                
                for node in company_data.get('nodes', []):
                    if node['id'] == edge['source']:
                        source_cluster = f"{node['type']}_{node['cluster']}"
                    if node['id'] == edge['target']:
                        target_cluster = f"{node['type']}_{node['cluster']}"
                
                if source_cluster and target_cluster:
                    edge_key = (source_cluster, target_cluster, edge['relation'])
                    self.edge_weights[edge_key] += 1
        
        # NetworkXグラフの構築
        self._build_networkx_graph()
    
    def _build_networkx_graph(self):
        """統合されたNetworkXグラフを構築"""
        # ノードの追加
        for cluster_id, data in self.cluster_data.items():
            self.integrated_graph.add_node(
                cluster_id,
                type=data['type'],
                count=data['count'],
                companies=list(data['companies']),
                texts=data['texts']
            )
        
        # エッジの追加
        for (source, target, relation), weight in self.edge_weights.items():
            if self.integrated_graph.has_edge(source, target):
                # 既存のエッジがある場合、関係を追加
                edge_data = self.integrated_graph[source][target]
                if 'relations' not in edge_data:
                    edge_data['relations'] = {}
                edge_data['relations'][relation] = weight
                edge_data['total_weight'] += weight
            else:
                # 新しいエッジの追加
                self.integrated_graph.add_edge(
                    source, target,
                    relations={relation: weight},
                    total_weight=weight
                )
    
    def generate_node_colors(self):
        """ノードタイプに基づいて色を生成"""
        type_colors = {
            'risk': '#FF6B6B',
            'opportunity': '#4ECDC4',
            'strategy': '#45B7D1',
            'target': '#96CEB4',
            'actual': '#FECA57'
        }
        return type_colors
    
    def create_interactive_visualization(self):
        """インタラクティブな可視化を作成"""
        # レイアウトの計算
        pos = nx.spring_layout(self.integrated_graph, k=3, iterations=50)
        
        # ノードの準備
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        node_info = []
        
        type_colors = self.generate_node_colors()
        
        for node in self.integrated_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            data = self.integrated_graph.nodes[node]
            node_type = data['type']
            count = data['count']
            companies = data['companies']
            
            # ノードサイズ（データ数に比例）
            node_size.append(max(20, count * 5))
            
            # ノード色
            node_color.append(type_colors.get(node_type, '#999999'))
            
            # ノードテキスト
            node_text.append(f"{node}<br>{node_type}<br>データ数: {count}")
            
            # 詳細情報の準備
            sample_texts = data['texts'][:3]  # 最初の3つのテキストをサンプルとして
            sample_text_str = "<br>".join([f"• {t['text'][:50]}..." for t in sample_texts])
            if len(data['texts']) > 3:
                sample_text_str += f"<br>... 他{len(data['texts']) - 3}件"
            
            info = f"""
            <b>クラスタ: {node}</b><br>
            <b>タイプ: {node_type}</b><br>
            <b>データ数: {count}</b><br>
            <b>関連企業数: {len(companies)}</b><br>
            <b>サンプルテキスト:</b><br>
            {sample_text_str}
            """
            node_info.append(info)
        
        # エッジの準備
        edge_x = []
        edge_y = []
        edge_info = []
        edge_width = []
        edge_color = []
        
        for edge in self.integrated_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            edge_data = self.integrated_graph[edge[0]][edge[1]]
            total_weight = edge_data['total_weight']
            relations = edge_data['relations']
            
            # エッジの幅（重みに比例）
            edge_width.append(max(1, total_weight * 2))
            
            # エッジの色（主要な関係タイプに基づく）
            main_relation = max(relations.items(), key=lambda x: x[1])[0]
            edge_color.append(self.relation_types[main_relation]['color'])
            
            # エッジ情報
            relations_str = "<br>".join([
                f"• {self.relation_types[rel]['description']}: {weight}回"
                for rel, weight in relations.items()
            ])
            
            info = f"""
            <b>{edge[0]} → {edge[1]}</b><br>
            <b>総接続数: {total_weight}</b><br>
            <b>関係の詳細:</b><br>
            {relations_str}
            """
            edge_info.append(info)
        
        # Plotlyでの可視化
        fig = go.Figure()
        
        # エッジの追加
        for i in range(0, len(edge_x), 3):
            if i + 1 < len(edge_x):
                fig.add_trace(go.Scatter(
                    x=[edge_x[i], edge_x[i+1]],
                    y=[edge_y[i], edge_y[i+1]],
                    mode='lines',
                    line=dict(
                        width=edge_width[i//3],
                        color=edge_color[i//3]
                    ),
                    hoverinfo='text',
                    hovertext=edge_info[i//3],
                    showlegend=False
                ))
        
        # ノードの追加
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white')
            ),
            text=[t.split('<br>')[0] for t in node_text],  # クラスタIDのみ表示
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hoverinfo='text',
            hovertext=node_info,
            showlegend=False
        ))
        
        # レイアウトの設定
        fig.update_layout(
            title=dict(
                text="日本上場企業サステナビリティデータ統合グラフ",
                x=0.5,
                font=dict(size=20)
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="ノードサイズ: データ数, エッジ幅: 接続頻度",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(size=12, color='grey')
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=800
        )
        
        return fig
    
    def create_summary_dashboard(self):
        """サマリーダッシュボードを作成"""
        # 統計情報の計算
        total_nodes = len(self.cluster_data)
        total_edges = len(self.edge_weights)
        total_companies = len(set().union(*[data['companies'] for data in self.cluster_data.values()]))
        
        # タイプ別統計
        type_stats = defaultdict(int)
        for data in self.cluster_data.values():
            type_stats[data['type']] += data['count']
        
        # 関係タイプ別統計
        relation_stats = defaultdict(int)
        for (_, _, relation), weight in self.edge_weights.items():
            relation_stats[relation] += weight
        
        # サブプロットの作成
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('タイプ別データ数', '関係タイプ別接続数', 'クラスタサイズ分布', '統計サマリー'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "table"}]]
        )
        
        # タイプ別データ数
        fig.add_trace(
            go.Bar(
                x=list(type_stats.keys()),
                y=list(type_stats.values()),
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
            ),
            row=1, col=1
        )
        
        # 関係タイプ別接続数
        fig.add_trace(
            go.Bar(
                x=[self.relation_types[k]['description'] for k in relation_stats.keys()],
                y=list(relation_stats.values()),
                marker_color=[self.relation_types[k]['color'] for k in relation_stats.keys()]
            ),
            row=1, col=2
        )
        
        # クラスタサイズ分布
        cluster_sizes = [data['count'] for data in self.cluster_data.values()]
        fig.add_trace(
            go.Histogram(
                x=cluster_sizes,
                nbinsx=20,
                marker_color='#45B7D1'
            ),
            row=2, col=1
        )
        
        # 統計サマリーテーブル
        fig.add_trace(
            go.Table(
                header=dict(values=['項目', '値'], fill_color='#f0f0f0'),
                cells=dict(
                    values=[
                        ['総クラスタ数', '総エッジ数', '総企業数', '平均クラスタサイズ', '最大クラスタサイズ'],
                        [total_nodes, total_edges, total_companies, 
                         f"{np.mean(cluster_sizes):.1f}", max(cluster_sizes)]
                    ],
                    fill_color='white'
                )
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="サステナビリティデータ統合分析ダッシュボード",
            height=800,
            showlegend=False
        )
        
        return fig
    
    def get_cluster_details(self, cluster_id):
        """特定のクラスタの詳細情報を取得"""
        if cluster_id not in self.cluster_data:
            return None
        
        data = self.cluster_data[cluster_id]
        return {
            'cluster_id': cluster_id,
            'type': data['type'],
            'count': data['count'],
            'companies': list(data['companies']),
            'texts': data['texts'],
            'connected_clusters': list(self.integrated_graph.neighbors(cluster_id))
        }

# 使用例
def demo_with_sample_data():
    """サンプルデータでのデモンストレーション"""
    
    # サンプルデータの生成
    sample_companies = [
        {
            "nodes": [
                {"id": "N1", "type": "risk", "text": "気候変動による物理的リスク", "cluster": "C1"},
                {"id": "N2", "type": "opportunity", "text": "再生可能エネルギー市場の拡大", "cluster": "C1"},
                {"id": "N3", "type": "strategy", "text": "カーボンニュートラル戦略", "cluster": "C1"},
                {"id": "N4", "type": "target", "text": "2030年CO2削減50%", "cluster": "C1"},
                {"id": "N5", "type": "actual", "text": "2023年CO2削減20%", "cluster": "C1"}
            ],
            "edges": [
                {"source": "N1", "target": "N3", "relation": "addresses_risk"},
                {"source": "N2", "target": "N3", "relation": "addresses_opportunity"},
                {"source": "N3", "target": "N4", "relation": "leads_to"},
                {"source": "N4", "target": "N5", "relation": "evaluated_by"}
            ]
        },
        {
            "nodes": [
                {"id": "N1", "type": "risk", "text": "規制強化による操業リスク", "cluster": "C1"},
                {"id": "N2", "type": "opportunity", "text": "ESG投資の増加", "cluster": "C1"},
                {"id": "N3", "type": "strategy", "text": "サステナブル経営の推進", "cluster": "C1"},
                {"id": "N4", "type": "target", "text": "ESGスコア向上", "cluster": "C1"},
                {"id": "N5", "type": "actual", "text": "ESGスコア15%向上", "cluster": "C1"}
            ],
            "edges": [
                {"source": "N1", "target": "N3", "relation": "addresses_risk"},
                {"source": "N2", "target": "N3", "relation": "addresses_opportunity"},
                {"source": "N3", "target": "N4", "relation": "leads_to"},
                {"source": "N4", "target": "N5", "relation": "evaluated_by"}
            ]
        }
    ]
    
    # 統合グラフの作成
    integrator = SustainabilityGraphIntegrator()
    integrator.load_company_data(sample_companies)
    
    # 可視化の生成
    main_fig = integrator.create_interactive_visualization()
    dashboard_fig = integrator.create_summary_dashboard()
    
    print("=== サステナビリティデータ統合グラフシステム ===")
    print(f"統合されたクラスタ数: {len(integrator.cluster_data)}")
    print(f"統合されたエッジ数: {len(integrator.edge_weights)}")
    print("\n統合グラフとダッシュボードが生成されました。")
    print("main_fig.show() でメイングラフを表示")
    print("dashboard_fig.show() でダッシュボードを表示")
    
    return integrator, main_fig, dashboard_fig

if __name__ == "__main__":
    integrator, main_fig, dashboard_fig = demo_with_sample_data()
    
    # グラフの表示
    main_fig.show()
    dashboard_fig.show()
    
    # 特定のクラスタの詳細表示例
    print("\n=== クラスタrisk_C1の詳細 ===")
    details = integrator.get_cluster_details("risk_C1")
    if details:
        print(f"タイプ: {details['type']}")
        print(f"データ数: {details['count']}")
        print(f"関連企業: {details['companies']}")
        print(f"接続先クラスタ: {details['connected_clusters']}")