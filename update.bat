@echo off
echo 🚀 Step 1: 正在同步最新房源数据...
python test_crawl.py

echo ☁️ Step 2: 正在发布至 GitHub (包含自动化配置)...
:: 强制修正远程仓库地址
git remote set-url origin https://github.com/Martin62300/havennest.git

:: 核心改动：使用 git add . 确保抓取所有文件，包括隐藏的 .github 文件夹
git add .
git commit -m "Deploy all-in-one services and GitHub Action: %date% %time%"

:: 强制推送到 master 分支
git push origin master -f

echo ✅ 任务完成！所有服务流程和凌晨自动更新逻辑已同步。
pause