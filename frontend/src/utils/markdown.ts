import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

export function renderMarkdown(raw: string): string {
  if (!raw) return ''
  const html = marked.parse(raw, { async: false }) as string
  return DOMPurify.sanitize(html)
}
