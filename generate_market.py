import os
import json
import yaml
import requests
from datetime import datetime
from github import Github, GithubException

# 从环境变量获取 GitHub Token
token = os.getenv('GITHUB_TOKEN')
if not token:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

# 初始化 GitHub 客户端
g = Github(token)

# 获取当前仓库的信息
# 注意：这里假设脚本运行在拥有所有目标仓库的组织或个人账户下
# 你需要明确指定要扫描的 GitHub 组织或用户名
repo_owner = "RO-Series"  # 请替换为你的组织或用户名

# 尝试获取用户或组织
try:
    user = g.get_user(repo_owner)
except GithubException:
    # 如果用户不存在，尝试作为组织获取
    user = g.get_organization(repo_owner)

# 获取所有仓库
repos = user.get_repos()

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
    if repo.name.startswith("ro_"):
        print(f"正在处理插件仓库: {repo.name}")
        
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
            
            print(f"  - 成功添加插件: {plugin_id}")
            
        except GithubException as e:
            print(f"  - 警告: 无法读取 metadata.yaml，跳过。错误: {e}")
        except yaml.YAMLError as e:
            print(f"  - 警告: metadata.yaml 格式错误，跳过。错误: {e}")

# 读取现有 market 文件，判断是否有变化
try:
    with open('plugin_market.json', 'r', encoding='utf-8') as f:
        old_content = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    old_content = {}

# 比较新旧数据
changes_made = (old_content != plugin_market)

# 写入新的 plugin_market.json 文件
with open('plugin_market.json', 'w', encoding='utf-8') as f:
    json.dump(plugin_market, f, indent=2, ensure_ascii=False)

# 设置一个输出变量，用于决定是否提交更改
# 注意：GITHUB_OUTPUT 是 GitHub Actions 特有的环境变量
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"changes={str(changes_made).lower()}")

print(f"市场索引已更新，共包含 {len(plugin_market)-1} 个插件。")
if changes_made:
    print("检测到内容变化，将在下一步提交更新。")
else:
    print("未检测到内容变化。")