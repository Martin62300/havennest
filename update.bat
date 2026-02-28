@echo off
echo 🚀 Step 1: 正在抓取最新房源 (Craigslist + Zumper)...
python test_crawl.py

echo ☁️ Step 2: 正在清理并上传数据到 GitHub...
git add .
git commit -m "Auto-update listings: %date% %time%"
git push origin main -f

echo ✅ 任务完成！你的 Havennest 网站已更新。
pause