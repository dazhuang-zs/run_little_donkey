<template>
  <div class="editor">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="video-panel">
          <template #header>
            <span>视频预览</span>
          </template>
          <video 
            ref="videoPlayer" 
            :src="videoUrl" 
            controls 
            class="video-player"
          ></video>
          <el-progress :percentage="progress" :status="progressStatus" />
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="script-panel">
          <template #header>
            <div class="script-header">
              <span>解说脚本</span>
              <el-button type="primary" @click="regenerateScript">
                重新生成
              </el-button>
            </div>
          </template>
          
          <el-input
            v-model="scriptContent"
            type="textarea"
            :rows="15"
            placeholder="解说脚本将在这里显示..."
          />
          
          <div class="script-actions">
            <el-button @click="previewVoice">
              试听配音
            </el-button>
            <el-button type="primary" @click="synthVideo">
              合成视频
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const projectId = route.params.projectId as string

const videoUrl = ref('')
const scriptContent = ref('')
const progress = ref(0)
const progressStatus = ref('')

onMounted(() => {
  // TODO: 加载项目数据
  loadProject()
})

const loadProject = async () => {
  // TODO: 从API加载项目数据
  ElMessage.info('加载项目中...')
}

const regenerateScript = async () => {
  // TODO: 重新生成脚本
  ElMessage.info('正在生成解说脚本...')
}

const previewVoice = () => {
  // TODO: 试听配音
  ElMessage.info('试听配音功能开发中...')
}

const synthVideo = async () => {
  // TODO: 合成视频
  progressStatus.value = 'success'
  progress.value = 100
  ElMessage.success('视频合成已启动！')
}
</script>

<style scoped>
.editor {
  padding: 20px;
}

.video-panel, .script-panel {
  background: rgba(255, 255, 255, 0.95);
}

.video-player {
  width: 100%;
  margin-bottom: 20px;
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.script-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>