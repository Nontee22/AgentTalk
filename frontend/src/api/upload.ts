import api from '@/api'
import type { UploadResponse } from '@/types/common'

export async function uploadImage(
  file: File,
  category: 'covers' | 'avatars' = 'covers',
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/upload', formData, {
    params: { category },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
