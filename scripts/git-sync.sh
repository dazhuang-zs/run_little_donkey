#!/bin/bash
# git-sync.sh - Git + Memory 同步脚本
# 实现本地与云端 OpenClaw 协同开发

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
MEMORY_FILES="MEMORY.md memory/*.md"
AUTO_COMMIT_MEMORY=true
AUTO_PUSH=true
COMMIT_PREFIX="[git-sync]"
MEMORY_DIR="memory"

# 帮助信息
show_help() {
    echo "用法: git-sync.sh <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  sync              完整同步（拉取 + 推送）"
    echo "  status            查看同步状态"
    echo "  checkpoint <msg>  创建工作检查点"
    echo "  resume            恢复工作状态"
    echo "  push-memory       仅推送 Memory 文件"
    echo "  pull-memory       仅拉取 Memory 文件"
    echo "  init              初始化 Memory 目录结构"
    echo "  help              显示帮助信息"
    echo ""
    echo "示例:"
    echo "  git-sync.sh sync"
    echo "  git-sync.sh checkpoint '完成了用户认证模块'"
    echo "  git-sync.sh status"
}

# 检查是否在 Git 仓库中
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        echo -e "${RED}错误: 当前目录不是 Git 仓库${NC}"
        exit 1
    fi
}

# 初始化 Memory 目录结构
init_memory() {
    echo -e "${BLUE}初始化 Memory 目录结构...${NC}"
    
    # 创建 memory 目录
    mkdir -p "$MEMORY_DIR"
    
    # 创建 MEMORY.md（如果不存在）
    if [ ! -f "MEMORY.md" ]; then
        cat > MEMORY.md << 'EOF'
# MEMORY.md - 长期记忆

## 项目概述

<!-- 记录项目的重要信息 -->

## 重要决策

<!-- 记录关键决策和原因 -->

## 架构设计

<!-- 记录架构相关内容 -->

## 待办事项

<!-- 长期待办事项 -->

## 工作状态

<!-- 当前工作状态，用于跨环境恢复 -->

### 最后更新
- 时间: 
- 环境: 
- 任务: 
- 进度: 

EOF
        echo -e "${GREEN}创建 MEMORY.md${NC}"
    fi
    
    # 创建每日日志文件
    TODAY=$(date +%Y-%m-%d)
    if [ ! -f "$MEMORY_DIR/$TODAY.md" ]; then
        cat > "$MEMORY_DIR/$TODAY.md" << EOF
# $TODAY 工作日志

## 今日任务


## 完成事项


## 遇到的问题


## 明日计划

EOF
        echo -e "${GREEN}创建 $MEMORY_DIR/$TODAY.md${NC}"
    fi
    
    # 创建 tasks.md
    if [ ! -f "$MEMORY_DIR/tasks.md" ]; then
        cat > "$MEMORY_DIR/tasks.md" << 'EOF'
# 待办事项

## 进行中


## 待处理


## 已完成

EOF
        echo -e "${GREEN}创建 $MEMORY_DIR/tasks.md${NC}"
    fi
    
    # 创建 context.md
    if [ ! -f "$MEMORY_DIR/context.md" ]; then
        cat > "$MEMORY_DIR/context.md" << 'EOF'
# 当前工作上下文

## 当前任务


## 相关文件


## 注意事项

EOF
        echo -e "${GREEN}创建 $MEMORY_DIR/context.md${NC}"
    fi
    
    echo -e "${GREEN}初始化完成！${NC}"
}

# 查看同步状态
show_status() {
    check_git_repo
    
    echo -e "${BLUE}=== Git 同步状态 ===${NC}"
    echo ""
    
    # 当前分支
    BRANCH=$(git branch --show-current)
    echo -e "当前分支: ${GREEN}$BRANCH${NC}"
    
    # Git 状态
    echo ""
    echo -e "${YELLOW}Git 状态:${NC}"
    if git diff-index --quiet HEAD --; then
        echo -e "  工作区: ${GREEN}干净${NC}"
    else
        echo -e "  工作区: ${YELLOW}有未提交的修改${NC}"
        git status --short | head -10
    fi
    
    # 远程状态
    echo ""
    echo -e "${YELLOW}远程状态:${NC}"
    git fetch --quiet 2>/dev/null || true
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse "@{u}" 2>/dev/null)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "  与远程: ${GREEN}同步${NC}"
    elif git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
        echo -e "  与远程: ${YELLOW}落后（需要 pull）${NC}"
    elif git merge-base --is-ancestor "$REMOTE" "$LOCAL" 2>/dev/null; then
        echo -e "  与远程: ${YELLOW}领先（需要 push）${NC}"
    else
        echo -e "  与远程: ${RED}分叉（需要 merge/rebase）${NC}"
    fi
    
    # Memory 文件状态
    echo ""
    echo -e "${YELLOW}Memory 文件:${NC}"
    if [ -f "MEMORY.md" ]; then
        LAST_UPDATE=$(grep -A1 "最后更新" MEMORY.md 2>/dev/null | tail -1 | sed 's/- //')
        echo -e "  MEMORY.md: ${GREEN}存在${NC}"
        [ -n "$LAST_UPDATE" ] && echo -e "    最后更新: $LAST_UPDATE"
    else
        echo -e "  MEMORY.md: ${RED}不存在${NC}"
    fi
    
    if [ -d "$MEMORY_DIR" ]; then
        FILE_COUNT=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
        echo -e "  memory/: ${GREEN}$FILE_COUNT 个文件${NC}"
    else
        echo -e "  memory/: ${RED}不存在${NC}"
    fi
}

# 完整同步
do_sync() {
    check_git_repo
    
    echo -e "${BLUE}=== 开始同步 ===${NC}"
    
    # 1. 拉取远程
    echo -e "${YELLOW}1. 拉取远程更新...${NC}"
    git fetch --quiet
    
    # 检查是否有冲突
    if git diff --quiet HEAD "@{u}" 2>/dev/null; then
        echo -e "   ${GREEN}本地已是最新${NC}"
    else
        # 暂存本地修改
        if ! git diff-index --quiet HEAD --; then
            echo -e "   ${YELLOW}暂存本地修改...${NC}"
            git stash push -m "git-sync auto stash"
            STASHED=true
        fi
        
        # 拉取并合并
        echo -e "   ${YELLOW}合并远程更新...${NC}"
        if git pull --quiet; then
            echo -e "   ${GREEN}合并成功${NC}"
        else
            echo -e "   ${RED}合并失败，可能存在冲突${NC}"
            [ "$STASHED" = true ] && git stash pop
            exit 1
        fi
        
        # 恢复暂存的修改
        if [ "$STASHED" = true ]; then
            echo -e "   ${YELLOW}恢复本地修改...${NC}"
            git stash pop
        fi
    fi
    
    # 2. 提交 Memory 文件
    if [ "$AUTO_COMMIT_MEMORY" = true ]; then
        echo -e "${YELLOW}2. 检查 Memory 文件...${NC}"
        MEMORY_CHANGED=false
        
        for file in MEMORY.md $MEMORY_DIR/*.md; do
            if [ -f "$file" ] && git diff --quiet HEAD -- "$file" 2>/dev/null; then
                :
            elif [ -f "$file" ]; then
                MEMORY_CHANGED=true
                git add "$file"
            fi
        done
        
        if [ "$MEMORY_CHANGED" = true ]; then
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
            git commit -m "$COMMIT_PREFIX 更新 Memory - $TIMESTAMP"
            echo -e "   ${GREEN}已提交 Memory 更新${NC}"
        else
            echo -e "   ${GREEN}Memory 无变化${NC}"
        fi
    fi
    
    # 3. 推送
    if [ "$AUTO_PUSH" = true ]; then
        echo -e "${YELLOW}3. 推送到远程...${NC}"
        if git push --quiet; then
            echo -e "   ${GREEN}推送成功${NC}"
        else
            echo -e "   ${RED}推送失败${NC}"
            exit 1
        fi
    fi
    
    echo ""
    echo -e "${GREEN}=== 同步完成 ===${NC}"
}

# 创建检查点
do_checkpoint() {
    check_git_repo
    
    if [ -z "$1" ]; then
        echo -e "${RED}错误: 请提供检查点信息${NC}"
        echo "用法: git-sync.sh checkpoint '检查点描述'"
        exit 1
    fi
    
    MESSAGE="$1"
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    ENVIRONMENT=$(hostname)
    
    echo -e "${BLUE}=== 创建检查点 ===${NC}"
    
    # 更新 MEMORY.md 中的工作状态
    if [ -f "MEMORY.md" ]; then
        # 使用 sed 更新工作状态部分
        if grep -q "### 最后更新" MEMORY.md; then
            # macOS 兼容的 sed
            sed -i '' "/### 最后更新/,/^$/c\\
### 最后更新\\
- 时间: $TIMESTAMP\\
- 环境: $ENVIRONMENT\\
- 任务: $MESSAGE\\
- 进度: 进行中\\
" MEMORY.md 2>/dev/null || sed -i "/### 最后更新/,/^$/c\\
### 最后更新\\
- 时间: $TIMESTAMP\\
- 环境: $ENVIRONMENT\\
- 任务: $MESSAGE\\
- 进度: 进行中\\
" MEMORY.md
        fi
        echo -e "${GREEN}已更新 MEMORY.md${NC}"
    fi
    
    # 提交所有修改
    echo -e "${YELLOW}提交所有修改...${NC}"
    git add -A
    git commit -m "$COMMIT_PREFIX 检查点: $MESSAGE ($TIMESTAMP)"
    
    # 推送
    echo -e "${YELLOW}推送到远程...${NC}"
    git push --quiet
    
    echo -e "${GREEN}检查点已创建并推送: $MESSAGE${NC}"
}

# 恢复工作状态
do_resume() {
    check_git_repo
    
    echo -e "${BLUE}=== 恢复工作状态 ===${NC}"
    
    # 拉取最新
    echo -e "${YELLOW}拉取最新代码...${NC}"
    git pull --quiet
    
    # 读取 MEMORY.md 中的工作状态
    if [ -f "MEMORY.md" ]; then
        echo ""
        echo -e "${GREEN}=== 上次工作状态 ===${NC}"
        grep -A5 "### 最后更新" MEMORY.md 2>/dev/null || echo "未找到工作状态记录"
        echo ""
        
        # 显示待办事项
        if [ -f "$MEMORY_DIR/tasks.md" ]; then
            echo -e "${YELLOW}=== 待办事项 ===${NC}"
            cat "$MEMORY_DIR/tasks.md"
            echo ""
        fi
        
        # 显示当前上下文
        if [ -f "$MEMORY_DIR/context.md" ]; then
            echo -e "${YELLOW}=== 当前上下文 ===${NC}"
            cat "$MEMORY_DIR/context.md"
        fi
    else
        echo -e "${YELLOW}MEMORY.md 不存在，建议先执行 init${NC}"
    fi
}

# 仅推送 Memory
push_memory() {
    check_git_repo
    
    echo -e "${BLUE}推送 Memory 文件...${NC}"
    
    for file in MEMORY.md $MEMORY_DIR/*.md; do
        if [ -f "$file" ]; then
            git add "$file"
        fi
    done
    
    if git diff --cached --quiet; then
        echo -e "${GREEN}Memory 无变化${NC}"
    else
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
        git commit -m "$COMMIT_PREFIX 更新 Memory - $TIMESTAMP"
        git push --quiet
        echo -e "${GREEN}Memory 已推送${NC}"
    fi
}

# 仅拉取 Memory
pull_memory() {
    check_git_repo
    
    echo -e "${BLUE}拉取 Memory 文件...${NC}"
    git fetch --quiet
    
    # 仅拉取 Memory 相关文件
    git checkout origin/$(git branch --show-current) -- MEMORY.md memory/*.md 2>/dev/null || \
        echo -e "${YELLOW}远程无 Memory 文件或已是最新${NC}"
    
    echo -e "${GREEN}Memory 已拉取${NC}"
}

# 主命令
case "$1" in
    sync)
        do_sync
        ;;
    status)
        show_status
        ;;
    checkpoint)
        do_checkpoint "$2"
        ;;
    resume)
        do_resume
        ;;
    push-memory)
        push_memory
        ;;
    pull-memory)
        pull_memory
        ;;
    init)
        init_memory
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
