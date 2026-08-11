import os
import json
import yaml
import requests
from datetime import datetime
from github import Github, GithubException, Auth

# 从环境变量获取 GitHub Token
token = os.getenv('GITHUB_TOKEN')
if not token:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

# 使用推荐的 Auth 方式（消除弃用警告）
auth = Auth.Token(token)
g = Github(auth=auth)

# 指定要扫描的组织或用户名
repo_owner = "RO-Series"

# 尝试获取用户或组织
try:
    # 先尝试作为用户获取
    user = g.get_user(repo_owner)
    print(f"作为用户获取成功: {user.name}")
except GithubException as e:
    print(f"用户获取失败，尝试作为组织获取...")
    try:
        # 如果用户获取失败，尝试作为组织获取
        user = g.get_organization(repo_owner)
        print(f"作为组织获取成功: {user.name}")
    except GithubException as e2:
        print(f"错误: 无法找到用户或组织 '{repo_owner}'")
        print(f"用户错误: {e}, 组织错误: {e2}")
        exit(1)

# 获取所有仓库
repos = user.get_repos()

# 统计和调试信息
repo_count = 0
ro_repo_count = 0
print(f"开始扫描 '{repo_owner}' 下的仓库...")

# 插件市场数据结构
plugin_market = {
    "$meta": {
        "schema_version": 1,
        "name": "RO系列_插件市场",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
}

# 扫描以 'ro_' 开头的插件仓库
for repo in repos:
    repo_count += 1
    print(f"检查仓库: {repo.name}")
    if repo.name.startswith("ro_") or repo.name.startswith("ro-"):
        ro_repo_count += 1
        print(f"  ✓ 找到插件仓库: {repo.name}")
        
        try:
            # 获取仓库根目录下的 metadata.yaml 文件内容
            contents = repo.get_contents("metadata.yaml")
            metadata_content = contents.decoded_content.decode('utf-8')
            metadata = yaml.safe_load(metadata_content)
            
            # 提取必要的插件信息
            author = metadata.get('author')
            name = metadata.get('name')
            version = metadata.get('version')
            desc = metadata.get('desc', '')
            
            # 构造 plugin_id
            plugin_id = f"{author}/{name}"
            
            # 添加到市场数据中
            plugin_market[plugin_id] = {
                "author": author,
                "name": name,
                "version": version,
                "repo": repo.html_url,
                "desc": desc,
                "updated_at": repo.updated_at.isoformat()
            }
            
            print(f"  - 成功添加插件: {plugin_id} (版本 {version})")
            
        except GithubException as e:
            print(f"  - 警告: 无法读取 metadata.yaml，跳过。错误: {e}")
        except yaml.YAMLError as e:
            print(f"  - 警告: metadata.yaml 格式错误，跳过。错误: {e}")
    else:
        print(f"  - 跳过: 不是插件仓库")

print(f"扫描完成: 共 {repo_count} 个仓库，其中 {ro_repo_count} 个以 'ro_' 开头")
