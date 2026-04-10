<template>
  <div class="home">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传视频</span>
        </div>
      </template>
      
      <el-upload
        class="video-uploader"
        drag
        :action="uploadUrl"
        :on-success="handleUploadSuccess"
        :before-upload="beforeUpload"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将视频文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 mp4/mov/avi 格式，文件大小不超过 500MB
          </div>
        </template>
      </el-upload>

      <div v-if="uploaded" class="options-section">
        <el-divider />
        
        <el-form label-width="80px">
          <el-form-item label="解说风格">
            <el-select v-model="selectedStyle" placeholder="选择解说风格">
              <el-option label="专业解说员" value="professional" />
              <el-option label="幽默吐槽风" value="humorous" />
              <el-option label="情感共情风" value="emotional" />
              <el-option label="悬疑推理风" value="suspense" />
              <el-option label="知识科普风" value="educational" />
            </el-select>
          </el-form-item>

          <el-form-item label="配音声音">
            <el-select v-model="selectedVoice" placeholder="选择配音声音">
              <el-option label="标准男声" value="male_standard" />
              <el-option label="磁性男声" value="male_deep" />
              <el-option label="甜美女声" value="female_sweet" />
              <el-option label="专业女声" value="female_professional" />
              <el-option label="卡通音色" value="special_cartoon" />
            </el-select>
          </el-form-item>
        </el-form>

        <el-button type="primary" size="large" @click="startProject">
          开始生成解说
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const uploadUrl = '/api/videos'
const uploaded = ref(false)
const selectedStyle = ref('professional')
const selectedVoice = ref('male_standard')
const videoId = ref('')

const beforeUpload = (file: File) => {
  const isValid = ['video/mp4', 'video/quicktime', 'video/x-msvideo'].includes(file.type)
  const isLt500M = file.size / 1024 / 1024 < 500

  if (!isValid) {
    ElMessage.error('只能上传 MP4/MOV/AVI 格式的视频!')
    return false
  }
  if (!isLt500M) {
    ElMessage.error('视频大小不能超过 500MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response: any) => {
  ElMessage.success('上传成功！')
  videoId.value = response.id
  uploaded.value = true
}

const startProject = () => {
  // TODO: 创建项目
  router.push(`/editor/${videoId.value}`)
}
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
}

.upload-card {
  background: rgba(255, 255, 255, 0.95);
}

.video-uploader {
  width: 100%;
}

.options-section {
  margin-top: 20px;
}
</style>