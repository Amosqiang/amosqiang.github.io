#!/bin/bash

echo "📝 一键上传 Jekyll 博客开始..."

git pull origin main   # 拉最新远程代码，防止冲突
git add .              # 添加所有更改

read -p "输入提交信息（留空自动填当前时间）：" msg
if [ -z "$msg" ]; then
    msg="更新于 $(date '+%Y-%m-%d %H:%M:%S')"
fi

git commit -m "$msg"   # 提交
git push origin main   # 推送到 GitHub

echo "✅ 上传完成"

