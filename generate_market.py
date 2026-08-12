import os
import json
import yaml
import requests
from datetime import datetime
from github import Github, Auth

def main():
    # 1. 配置和初始化
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("错误: 环境变量 GITHUB_TOKEN 未设置")
    
    repo_owner = "RO-Series"  # 你的GitHub组织或用户名
    market_file = "plugin_market.json"
    
    # 使用推荐的认证方式
    auth = Auth.Token(token)
    g = Github(auth=auth)

    # 2. 获取目标用户或组织
    try:
        user = g.get_user(repo_owner)
        print(f"作为用户获取成功: {user.name or repo_owner}")
    except Exception:
        try:
            user = g.get_organization(repo_owner)
            print(f"作为组织获取成功: {user.name or repo_owner}")
        except Exception as e:
            print(f"错误: 无法找到用户或组织 '{repo_owner}'")
            print(f"详细信息: {e}")
            return

    # 3. 初始化市场数据
    plugin_market = {
        "$meta": {
            "schema_version": 1,
            "name": "RO系列_插件市场",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

    # 4. 扫描并处理仓库
    repos = user.get_repos()
    repo_count = 0
    plugin_count = 0
    
    print(f"\n开始扫描 '{repo_owner}' 下的仓库...")
    
    for repo in repos:
        repo_count += 1
        repo_name = repo.name
        print(f"\n检查仓库: {repo_name}")
        
        # 判断是否为插件仓库 (以 ro_ 或 ro- 开头)
        if not (repo_name.startswith("ro_") or repo_name.startswith("ro-")):
            print(f"  - 跳过: 不是插件仓库 (前缀不符)")
            continue
            
        print(f"  ✓ 发现插件仓库")
        plugin_count += 1
        
        # 5. 通过原始URL读取 metadata.yaml (你建议的方式)
        metadata_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/metadata.yaml"
        print(f"  - 尝试读取: {metadata_url}")
        
        try:
            response = requests.get(metadata_url, timeout=10)
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            
            metadata_content = response.text
            metadata = yaml.safe_load(metadata_content)
            
            if not metadata:
                print(f"  - 警告: metadata.yaml 内容为空，跳过")
                continue
                
            # 提取必要字段
            author = metadata.get('author')
            name = metadata.get('name')
            version = metadata.get('version')
            desc = metadata.get('desc', '')
            
            # 验证必要字段
            if not all([author, name, version]):
                print(f"  - 警告: metadata.yaml 缺少必要字段 (author/name/version)，跳过")
                continue
            
            # 构造 plugin_id 并添加到市场
            plugin_id = f"{author}/{name}"
            plugin_market[plugin_id] = {
                "author": author,
                "name": name,
                "version": version,
                "repo": repo.html_url,
                "desc": desc,
                "updated_at": repo.updated_at.isoformat()
            }
            
            print(f"  - 成功添加插件: {plugin_id} (版本 {version})")
            
        except requests.exceptions.RequestException as e:
            print(f"  - 错误: 无法获取 metadata.yaml (网络问题: {e})")
        except yaml.YAMLError as e:
            print(f"  - 错误: metadata.yaml 格式错误 (YAML解析失败: {e})")
        except Exception as e:
            print(f"  - 错误: 处理过程中出现未知异常: {e}")

    # 6. 统计和输出
    print(f"\n扫描完成: 共 {repo_count} 个仓库，其中 {plugin_count} 个插件仓库")
    print(f"成功添加到市场的插件数: {len(plugin_market) - 1}")

    # 7. 安全地写入文件
    # 如果没有任何插件数据，但文件已存在，则保持原有内容不变
    if len(plugin_market) <= 1:  # 只有 $meta
        print("\n警告: 未找到任何有效的插件，将尝试保留现有市场文件")
        try:
            with open(market_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            if existing_data and len(existing_data) > 1:
                plugin_market = existing_data
                print(f"已从现有文件恢复 {len(plugin_market) - 1} 个插件")
            else:
                print("现有文件也为空或不存在，将创建空市场索引")
        except (FileNotFoundError, json.JSONDecodeError):
            print("没有可恢复的现有文件，将创建仅包含 $meta 的市场索引")
    else:
        # 读取旧文件以判断是否有变化
        try:
            with open(market_file, 'r', encoding='utf-8') as f:
                old_content = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            old_content = {}
        
        # 比较新旧内容
        changes_made = (old_content != plugin_market)
        print(f"\n内容是否发生变化: {changes_made}")

    # 8. 写入最终文件
    with open(market_file, 'w', encoding='utf-8') as f:
        json.dump(plugin_market, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 市场索引已写入: {market_file}")
    print(f"最终包含 {len(plugin_market) - 1} 个插件")

if __name__ == "__main__":
    main()
