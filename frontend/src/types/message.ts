export interface Message {
  role: 'user' | 'agent' | 'admin' | 'system' | 'tools'
  content: string
}
