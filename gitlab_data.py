import gitlab
import json
from datetime import datetime
import pandas as pd
import time

class GitLabDeveloperExtractor:
    def __init__(self, access_token=None):
        """
        初始化GitLab客户端
        access_token: GitLab访问令牌，如果没有提供则使用公共访问
        """
        if access_token:
            # Corrected: Call the Gitlab class from the 'gitlab' library
            self.gl = gitlab.Gitlab('https://gitlab.com', private_token=access_token)
        else:
            # Corrected: Call the Gitlab class from the 'gitlab' library
            self.gl = gitlab.Gitlab('https://gitlab.com')
        
    def get_project(self, project_id):
        """获取项目对象"""
        try:
            project = self.gl.projects.get(project_id)
            return project
        except Exception as e:
            print(f"获取项目失败: {e}")
            return None
    
    def extract_commits(self, project):
        """抽取所有提交信息"""
        print("正在抽取提交信息...")
        commits_data = []
        
        try:
            # 获取所有提交，按时间倒序
            commits = project.commits.list(all=True, order_by='committed_date', sort='desc')
            
            for commit in commits:
                commit_detail = project.commits.get(commit.id)
                
                commits_data.append({
                    'event_type': 'commit',
                    'developer_name': commit_detail.author_name,
                    'developer_email': commit_detail.author_email,
                    'committer_name': commit_detail.committer_name,
                    'committer_email': commit_detail.committer_email,
                    'timestamp': commit_detail.authored_date,
                    'commit_id': commit_detail.id,
                    'title': commit_detail.title,
                    'message': commit_detail.message,
                    'stats': commit_detail.stats,
                    'web_url': commit_detail.web_url
                })
                
                # 添加延迟以避免API限制
                time.sleep(0.1)
                
        except Exception as e:
            print(f"抽取提交信息时出错: {e}")
            
        return commits_data
    
    def extract_merge_requests(self, project):
        """抽取所有合并请求信息"""
        print("正在抽取合并请求信息...")
        mr_data = []
        
        try:
            # 获取所有合并请求
            merge_requests = project.mergerequests.list(
                all=True, 
                state='all',  # 包括打开、关闭、合并的所有状态
                order_by='updated_at',
                sort='desc'
            )
            
            for mr in merge_requests:
                mr_detail = project.mergerequests.get(mr.id)
                
                # MR创建事件
                mr_data.append({
                    'event_type': 'merge_request_created',
                    'developer_name': mr_detail.author['name'],
                    'developer_email': mr_detail.author.get('email', ''),
                    'developer_username': mr_detail.author['username'],
                    'timestamp': mr_detail.created_at,
                    'mr_id': mr_detail.iid,
                    'title': mr_detail.title,
                    'description': mr_detail.description,
                    'state': mr_detail.state,
                    'source_branch': mr_detail.source_branch,
                    'target_branch': mr_detail.target_branch,
                    'web_url': mr_detail.web_url
                })
                
                # MR合并事件（如果已合并）
                if mr_detail.state == 'merged' and mr_detail.merged_by:
                    mr_data.append({
                        'event_type': 'merge_request_merged',
                        'developer_name': mr_detail.merged_by['name'],
                        'developer_email': mr_detail.merged_by.get('email', ''),
                        'developer_username': mr_detail.merged_by['username'],
                        'timestamp': mr_detail.merged_at,
                        'mr_id': mr_detail.iid,
                        'title': mr_detail.title,
                        'web_url': mr_detail.web_url
                    })
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"抽取合并请求信息时出错: {e}")
            
        return mr_data
    
    def extract_issues(self, project):
        """抽取所有问题信息"""
        print("正在抽取问题信息...")
        issues_data = []
        
        try:
            issues = project.issues.list(
                all=True,
                state='all',
                order_by='updated_at',
                sort='desc'
            )
            
            for issue in issues:
                issue_detail = project.issues.get(issue.id)
                
                # Issue创建事件
                issues_data.append({
                    'event_type': 'issue_created',
                    'developer_name': issue_detail.author['name'],
                    'developer_email': issue_detail.author.get('email', ''),
                    'developer_username': issue_detail.author['username'],
                    'timestamp': issue_detail.created_at,
                    'issue_id': issue_detail.iid,
                    'title': issue_detail.title,
                    'description': issue_detail.description,
                    'state': issue_detail.state,
                    'labels': issue_detail.labels,
                    'web_url': issue_detail.web_url
                })
                
                # Issue关闭事件（如果已关闭且有关闭者）
                if issue_detail.state == 'closed' and issue_detail.closed_by:
                    issues_data.append({
                        'event_type': 'issue_closed',
                        'developer_name': issue_detail.closed_by['name'],
                        'developer_email': issue_detail.closed_by.get('email', ''),
                        'developer_username': issue_detail.closed_by['username'],
                        'timestamp': issue_detail.closed_at,
                        'issue_id': issue_detail.iid,
                        'title': issue_detail.title,
                        'web_url': issue_detail.web_url
                    })
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"抽取问题信息时出错: {e}")
            
        return issues_data
    
    def extract_project_members(self, project):
        """抽取项目成员信息"""
        print("正在抽取项目成员信息...")
        members_data = []
        
        try:
            members = project.members.list(all=True)
            
            for member in members:
                members_data.append({
                    'event_type': 'project_membership',
                    'developer_name': member.name,
                    'developer_email': member.email if hasattr(member, 'email') else '',
                    'developer_username': member.username,
                    'access_level': member.access_level,
                    'access_level_description': self._get_access_level_name(member.access_level)
                })
                
        except Exception as e:
            print(f"抽取项目成员信息时出错: {e}")
            
        return members_data
    
    def _get_access_level_name(self, level):
        """获取访问级别名称"""
        levels = {
            10: 'Guest',
            20: 'Reporter', 
            30: 'Developer',
            40: 'Maintainer',
            50: 'Owner'
        }
        return levels.get(level, f'Level {level}')
    
    def extract_all_events(self, project_id_or_path):
        """抽取所有开发者事件"""
        project = self.get_project(project_id_or_path)
        if not project:
            return None
        
        print(f"开始抽取项目 '{project.name}' 的开发者事件...")
        print(f"项目URL: {project.web_url}")
        
        all_events = []
        
        # 抽取各种类型的事件
        commits = self.extract_commits(project)
        merge_requests = self.extract_merge_requests(project)
        issues = self.extract_issues(project)
        members = self.extract_project_members(project)
        
        all_events.extend(commits)
        all_events.extend(merge_requests)
        all_events.extend(issues)
        all_events.extend(members)
        
        # 按时间戳排序（如果有时间戳）
        events_with_time = [e for e in all_events if 'timestamp' in e and e['timestamp']]
        events_without_time = [e for e in all_events if 'timestamp' not in e or not e['timestamp']]
        
        events_with_time.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events_with_time + events_without_time
    
    def save_events_to_files(self, events, filename_prefix="bitcoin_cash_node_events"):
        """保存事件到文件"""
        if not events:
            print("没有事件数据可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"事件数据已保存到 {json_filename}")
        
        # 保存为CSV
        try:
            df = pd.DataFrame(events)
            csv_filename = f"{filename_prefix}_{timestamp}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"事件数据已保存到 {csv_filename}")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
        
        return json_filename, csv_filename
    
    def analyze_developers(self, events):
        """分析开发者活动"""
        if not events:
            return {}
        
        developer_stats = {}
        
        for event in events:
            dev_name = event.get('developer_name', 'Unknown')
            dev_email = event.get('developer_email', '')
            event_type = event.get('event_type', '')
            
            if dev_name not in developer_stats:
                developer_stats[dev_name] = {
                    'name': dev_name,
                    'email': dev_email,
                    'username': event.get('developer_username', ''),
                    'total_events': 0,
                    'event_types': {},
                    'first_activity': None,
                    'last_activity': None
                }
            
            stats = developer_stats[dev_name]
            stats['total_events'] += 1
            
            # 统计事件类型
            if event_type in stats['event_types']:
                stats['event_types'][event_type] += 1
            else:
                stats['event_types'][event_type] = 1
            
            # 更新活动时间
            if 'timestamp' in event and event['timestamp']:
                if not stats['first_activity'] or event['timestamp'] < stats['first_activity']:
                    stats['first_activity'] = event['timestamp']
                if not stats['last_activity'] or event['timestamp'] > stats['last_activity']:
                    stats['last_activity'] = event['timestamp']
        
        return developer_stats

# 使用示例
def main():
    # 初始化抽取器
    # 如果你有GitLab访问令牌，可以传入以获取更多数据
    # extractor = GitLabDeveloperExtractor(access_token='your_token_here')
    extractor = GitLabDeveloperExtractor()
    
    # Bitcoin Cash Node项目ID
    project_path = 'bitcoin-cash-node/bitcoin-cash-node'
    
    try:
        # 抽取所有事件
        events = extractor.extract_all_events(project_path)
        
        if events:
            print(f"\n成功抽取了 {len(events)} 个开发者事件")
            
            # 保存到文件
            extractor.save_events_to_files(events)
            
            # 分析开发者活动
            developer_stats = extractor.analyze_developers(events)
            
            print(f"\n发现 {len(developer_stats)} 个开发者:")
            for dev_name, stats in sorted(developer_stats.items(), 
                                        key=lambda x: x[1]['total_events'], 
                                        reverse=True)[:10]:  # 显示前10个最活跃的开发者
                print(f"\n开发者: {stats['name']}")
                print(f"  邮箱: {stats['email']}")
                print(f"  用户名: {stats['username']}")
                print(f"  总事件数: {stats['total_events']}")
                print(f"  事件类型: {stats['event_types']}")
                if stats['first_activity']:
                    print(f"  首次活动: {stats['first_activity']}")
                if stats['last_activity']:
                    print(f"  最近活动: {stats['last_activity']}")
            
            # 显示最近几个事件示例
            print(f"\n最近的事件示例:")
            for i, event in enumerate(events[:5]):  # 显示前5个最近事件
                print(f"\n事件 {i+1}:")
                print(f"  类型: {event.get('event_type', 'Unknown')}")
                print(f"  开发者: {event.get('developer_name', 'Unknown')}")
                print(f"  时间: {event.get('timestamp', 'Unknown')}")
                if 'title' in event:
                    print(f"  标题: {event['title'][:100]}...")
                if 'web_url' in event:
                    print(f"  链接: {event['web_url']}")
        
    except Exception as e:
        print(f"执行过程中出错: {e}")

# 高级功能：获取更详细的事件信息
def extract_detailed_events(access_token=None):
    """抽取更详细的事件信息，包括评论、标签等"""
    extractor = GitLabDeveloperExtractor(access_token)
    project_path = 'bitcoin-cash-node/bitcoin-cash-node'
    
    project = extractor.get_project(project_path)
    if not project:
        return
    
    detailed_events = []
    
    # 获取Issues的详细活动
    print("正在获取Issues的详细活动...")
    try:
        issues = project.issues.list(all=True, state='all')
        for issue in issues[:50]:  # 限制数量以避免超时
            issue_detail = project.issues.get(issue.id)
            
            # 获取Issue的评论
            try:
                notes = issue_detail.notes.list(all=True)
                for note in notes:
                    if hasattr(note, 'author'):
                        detailed_events.append({
                            'event_type': 'issue_comment',
                            'developer_name': note.author['name'],
                            'developer_username': note.author['username'],
                            'timestamp': note.created_at,
                            'issue_id': issue.iid,
                            'issue_title': issue.title,
                            'comment_body': note.body[:200] + '...' if len(note.body) > 200 else note.body,
                            'web_url': issue.web_url + f"#note_{note.id}"
                        })
            except:
                pass
            
            time.sleep(0.1)
    except Exception as e:
        print(f"获取Issues详细信息时出错: {e}")
    
    return detailed_events

# 数据导出功能
def export_developer_summary(events, filename="developer_summary.json"):
    """导出开发者活动汇总"""
    developer_summary = {}
    
    for event in events:
        dev_name = event.get('developer_name', 'Unknown')
        
        if dev_name not in developer_summary:
            developer_summary[dev_name] = {
                'name': dev_name,
                'email': event.get('developer_email', ''),
                'username': event.get('developer_username', ''),
                'activities': []
            }
        
        activity = {
            'type': event.get('event_type'),
            'timestamp': event.get('timestamp'),
            'title': event.get('title', ''),
            'url': event.get('web_url', '')
        }
        
        developer_summary[dev_name]['activities'].append(activity)
    
    # 按活动数量排序
    sorted_developers = dict(sorted(developer_summary.items(), 
                                  key=lambda x: len(x[1]['activities']), 
                                  reverse=True))
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sorted_developers, f, ensure_ascii=False, indent=2)
    
    print(f"开发者汇总已保存到 {filename}")
    return sorted_developers

if __name__ == "__main__":
    main()
    
    # 如果你想要更详细的事件信息，取消注释下面的代码
    # detailed_events = extract_detailed_events()
    # if detailed_events:
    #     export_developer_summary(detailed_events, "detailed_developer_summary.json")