import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { Archive, ArrowUp, ChevronDown, Command, FileCode2, FolderKanban, Gauge, Layers3, Menu, Mic, MoreHorizontal, Plus, Search, Settings2, ShieldAlert, Sparkles, SquareTerminal, SunMedium, X } from 'lucide-react'

type Message = { role: 'user' | 'assistant'; text: string; activity?: string }
type BridgeEvent = { type: string; text?: string; name?: string; status?: string; id?: string; tool?: string; arguments?: Record<string, unknown>; message?: string; detail?: string; model?: string; provider?: string; items?: any[]; messages?: any[]; settings?: { personalization?: string; system_prompt?: string } }
type Provider = { id: string; label: string; model: string }
type Memory = { id: string; content: string; category?: string; tags?: string[]; updated_at?: string }
type Attachment = { name: string; kind: 'file' | 'screenshot'; content?: string }

const providers: Provider[] = [
  { id: 'local', label: 'Local', model: 'LM Studio' },
  { id: 'groq', label: 'Groq', model: 'Groq hosted' },
  { id: 'gemini', label: 'Gemini Flash 3.6', model: 'Gemini Flash 3.6' },
  { id: 'qwen', label: 'Qwen 3.8 Flash', model: 'Qwen 3.8 Flash' },
]
const fallbackChats = ['Merapikan workspace Astral', 'Riset arsitektur GUI modern', 'Roadmap versi 2.x', 'Membuat tool file manager']

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [prompt, setPrompt] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [bridgeReady, setBridgeReady] = useState(false)
  const [activity, setActivity] = useState('')
  const [notice, setNotice] = useState('')
  const [permission, setPermission] = useState<BridgeEvent | null>(null)
  const [provider, setProvider] = useState('local')
  const [modelOpen, setModelOpen] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [lightMode, setLightMode] = useState(false)
  const [history, setHistory] = useState<{ id: string; title: string; updated_at?: string }[]>([])
  const [panel, setPanel] = useState<'memory' | 'settings' | 'errors' | 'apps' | null>(null)
  const [memories, setMemories] = useState<Memory[]>([])
  const [memoryDraft, setMemoryDraft] = useState<Memory | null>(null)
  const [errors, setErrors] = useState<any[]>([])
  const [apps, setApps] = useState<any[]>([])
  const [personalization, setPersonalization] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  const selected = providers.find((item) => item.id === provider) || providers[0]
  const chats: { id: string; title: string; updated_at?: string }[] = history.length ? history : fallbackChats.map((title, index) => ({ id: `demo-${index}`, title }))
  const visibleChats = chats.filter((item) => item.title.toLowerCase().includes(search.toLowerCase()))

  useEffect(() => {
    if (!('__TAURI_INTERNALS__' in window)) return
    invoke<boolean>('bridge_status').then(setBridgeReady).catch(() => setBridgeReady(false))
    const send = (type: string) => invoke('bridge_command', { command: { type } }).catch(() => undefined)
    const unlisten = listen<BridgeEvent>('astral-event', ({ payload }) => {
      if (payload.type === 'bridge_ready' || payload.type === 'provider_changed') { setBridgeReady(true); if (payload.provider) setProvider(payload.provider) }
      if (payload.type === 'thinking') setActivity(payload.status || 'working...')
      if (payload.type === 'thinking_end') setActivity('')
      if (payload.type === 'tool_start') setActivity(`Running ${payload.name || 'tool'}...`)
      if (payload.type === 'tool_complete') setActivity('')
      if (payload.type === 'permission_required') setPermission(payload)
      if (payload.type === 'response_start') setMessages((current) => current.at(-1)?.role === 'assistant' && current.at(-1)?.text === '' ? current : [...current, { role: 'assistant', text: '' }])
      if (payload.type === 'token') setMessages((current) => { const next = [...current]; const last = next.at(-1); if (!last || last.role !== 'assistant') next.push({ role: 'assistant', text: payload.text || '' }); else last.text += payload.text || ''; return next })
      if (payload.type === 'complete') setMessages((current) => { const next = [...current]; const last = next.at(-1); if (last?.role === 'assistant') last.text = payload.text || last.text; else if (payload.text) next.push({ role: 'assistant', text: payload.text }); return next })
      if (['complete', 'response_end'].includes(payload.type)) { setIsThinking(false); setActivity('') }
      if (payload.type === 'session_reset') { setMessages([]); setIsThinking(false) }
      if (payload.type === 'error') { setErrors((current) => [{ message: payload.message, detail: payload.detail, time: new Date().toISOString() }, ...current]); setMessages((current) => [...current, { role: 'assistant', text: `${payload.message || 'Terjadi kesalahan.'}${payload.detail ? `\n\n${payload.detail}` : ''}` }]); setIsThinking(false); setActivity('') }
      if (payload.type === 'history_list') setHistory(payload.items || [])
      if (payload.type === 'history_loaded') setMessages((payload.messages || []).map((item: any) => ({ role: item.role, text: item.text ?? item.content ?? '' })) as Message[])
      if (['memory_list', 'memory_saved', 'memory_deleted'].includes(payload.type)) setMemories(payload.items || [])
      if (payload.type === 'settings') { setPersonalization(payload.settings?.personalization || ''); setSystemPrompt(payload.settings?.system_prompt || '') }
      if (payload.type === 'error_log') setErrors(payload.items || [])
      if (payload.type === 'apps_list') setApps(payload.items || [])
    })
    send('history_list'); send('settings_get')
    return () => { unlisten.then((stop) => stop()) }
  }, [])

  const greeting = useMemo(() => { const hour = new Date().getHours(); return hour < 11 ? 'Selamat pagi, bos.' : hour < 15 ? 'Selamat siang, bos.' : hour < 19 ? 'Selamat sore, bos.' : 'Selamat malam, bos.' }, [])
  const bridgeCommand = (command: Record<string, unknown>) => invoke('bridge_command', { command })
  const flash = (text: string) => { setNotice(text); window.setTimeout(() => setNotice(''), 2400) }

  function submit(event: FormEvent) {
    event.preventDefault(); const text = prompt.trim(); if (!text || isThinking) return
    setMessages((current) => [...current, { role: 'user', text }]); setPrompt(''); setAttachments([]); setIsThinking(true)
    if (bridgeReady) bridgeCommand({ type: 'user_message', text, attachments }).catch((error) => { flash(String(error)); setIsThinking(false) })
    else window.setTimeout(() => { setMessages((current) => [...current, { role: 'assistant', text: 'Jalankan Astral melalui Tauri untuk menghubungkan Agent Python.', activity: 'Tauri bridge belum aktif' }]); setIsThinking(false) }, 500)
  }
  function openPanel(name: 'memory' | 'settings' | 'errors' | 'apps') { setPanel(name); const type = { memory: 'memory_list', settings: 'settings_get', errors: 'error_log', apps: 'apps_list' }[name]; bridgeCommand({ type }).catch(() => undefined) }
  function insertFiles(files: FileList | null) { if (!files) return; Array.from(files).forEach((file) => { if (file.type.startsWith('image/')) { const reader = new FileReader(); reader.onload = () => setAttachments((current) => [...current, { name: file.name, kind: 'screenshot', content: String(reader.result) }]); reader.readAsDataURL(file) } else file.text().then((content) => setAttachments((current) => [...current, { name: file.name, kind: 'file', content: content.slice(0, 12000) }])) }) }
  async function insertScreenshot() { try { for (const item of await navigator.clipboard.read()) for (const type of item.types) if (type.startsWith('image/')) { const reader = new FileReader(); reader.onload = () => setAttachments((current) => [...current, { name: `screenshot-${Date.now()}.png`, kind: 'screenshot', content: String(reader.result) }]); reader.readAsDataURL(await item.getType(type)); return } flash('Tidak ada screenshot di clipboard') } catch { flash('Gunakan Ctrl+V untuk menempel screenshot') } }
  function saveSettings() { bridgeCommand({ type: 'settings_save', personalization, system_prompt: systemPrompt }).catch(() => undefined); setPanel(null) }
  function saveMemory() { if (memoryDraft?.content.trim()) bridgeCommand({ type: 'memory_save', id: memoryDraft.id, content: memoryDraft.content, category: memoryDraft.category || 'general', tags: memoryDraft.tags || [] }).catch(() => undefined); setMemoryDraft(null) }

  return <main className={`app-shell ${lightMode ? 'app-shell--light' : ''}`}>
    <aside className={`sidebar ${sidebarOpen ? '' : 'sidebar--closed'}`}><div className="sidebar-topbar"><button className="brand-lockup" onClick={() => setSidebarOpen(true)}><span className="astral-mark"><Sparkles size={16} /></span><span className="brand-name">ASTRAL</span></button><button className="icon-button subtle" onClick={() => setSidebarOpen(false)}><X size={17} /></button></div><div className="sidebar-actions"><button className="new-chat" onClick={() => { setMessages([]); bridgeCommand({ type: 'new_chat' }).catch(() => undefined) }}><Plus size={16} /> New chat</button>{searchOpen ? <div className="search-field"><Search size={15} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari..." /><button onClick={() => { setSearchOpen(false); setSearch('') }}><X size={13} /></button></div> : <button className="nav-item" onClick={() => setSearchOpen(true)}><Search size={16} /> Cari percakapan <kbd>Ctrl K</kbd></button>}</div><div className="sidebar-section"><div className="section-label"><span>Percakapan</span><MoreHorizontal size={16} /></div><div className="conversation-list">{visibleChats.map((chat, index) => <button className={`conversation ${index === 0 ? 'conversation--active' : ''}`} key={chat.id} onClick={() => chat.id.startsWith('demo-') ? flash(chat.title) : bridgeCommand({ type: 'history_load', id: chat.id })}><span className="conversation-dot" /><span className="conversation-copy"><strong>{chat.title}</strong><small>{chat.updated_at ? 'Tersimpan' : 'Demo'}</small></span></button>)}</div></div><div className="sidebar-section sidebar-section--lower"><div className="section-label"><span>Workspace</span></div><button className="nav-item" onClick={() => flash('File browser akan terhubung ke workspace')}><FolderKanban size={16} /> Files</button><button className="nav-item" onClick={() => openPanel('memory')}><Archive size={16} /> Memory</button><button className="nav-item" onClick={() => openPanel('errors')}><Gauge size={16} /> Error log</button><button className="nav-item" onClick={() => openPanel('apps')}><SquareTerminal size={16} /> App launcher</button></div><div className="sidebar-footer"><button className="profile-button" onClick={() => openPanel('settings')}><span className="avatar">A</span><span><strong>astral</strong><small>Local workspace</small></span><ChevronDown size={15} /></button><button className="icon-button subtle" onClick={() => openPanel('settings')}><Settings2 size={17} /></button></div></aside>
    <section className="main-panel"><header className="topbar">{!sidebarOpen && <button className="icon-button" onClick={() => setSidebarOpen(true)}><Menu size={18} /></button>}<div className="topbar-context"><span className="status-dot" /> Local agent <span className="slash">/</span> <span className="muted">Workspace</span></div><div className="topbar-actions"><button className="icon-button" onClick={() => setLightMode((value) => !value)} title="Toggle light mode"><SunMedium size={17} /></button><div className="more-wrap"><button className="icon-button" onClick={() => setMoreOpen((value) => !value)}><MoreHorizontal size={18} /></button>{moreOpen && <div className="popover top-popover"><button onClick={() => openPanel('errors')}>Error log</button><button onClick={() => openPanel('settings')}>Settings</button></div>}</div></div></header><div className={`chat-area ${messages.length ? 'chat-area--active' : ''}`}>{messages.length === 0 ? <div className="welcome-state"><div className="welcome-orb"><Sparkles size={30} /></div><p className="eyebrow">LOCAL-FIRST · READY TO HELP</p><h1>{greeting}</h1><p className="welcome-copy">Apa yang ingin kamu kerjakan hari ini?</p></div> : <div className="message-stack">{messages.map((message, index) => <article className={`message message--${message.role}`} key={`${message.role}-${index}`}><div className="message-avatar">{message.role === 'user' ? 'A' : <Sparkles size={15} />}</div><div className="message-body"><div className="message-meta">{message.role === 'user' ? 'Kamu' : 'Astral'}</div><p>{message.text}</p>{message.activity && <div className="activity-pill"><span className="activity-pulse" />{message.activity}</div>}</div></article>)}{isThinking && <div className="thinking-row"><span className="thinking-mark"><Sparkles size={15} /></span><span className="thinking-dots"><i /><i /><i /></span><span>{activity || 'working...'}</span></div>}</div>}<div className="composer-wrap"><form className="composer" onSubmit={submit}><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} onPaste={(event) => { if (event.clipboardData.files.length) { event.preventDefault(); insertFiles(event.clipboardData.files) } }} placeholder="Tulis pesan untuk Astral..." rows={1} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(event) } }} /><div className="composer-bottom"><div className="composer-tools"><button type="button" className="round-tool" onClick={() => fileInput.current?.click()}><Plus size={18} /></button><button type="button" className="tool-chip" onClick={() => fileInput.current?.click()}><FileCode2 size={15} /> Insert file</button><button type="button" className="tool-chip" onClick={insertScreenshot}>Insert ss</button><input ref={fileInput} hidden type="file" multiple onChange={(event) => { insertFiles(event.target.files); event.currentTarget.value = '' }} /></div><div className="composer-model"><div className="model-wrap"><button type="button" className="model-picker" onClick={() => setModelOpen((value) => !value)}>{selected.label}<ChevronDown size={14} /></button>{modelOpen && <div className="popover model-popover">{providers.map((item) => <button type="button" key={item.id} className={item.id === provider ? 'selected' : ''} onClick={() => { setProvider(item.id); setModelOpen(false); bridgeCommand({ type: 'set_provider', provider: item.id }).catch(() => undefined) }}><span><strong>{item.label}</strong><small>{item.model}</small></span>{item.id === provider && <span className="check">✓</span>}</button>)}</div>}</div><button type="button" className="round-tool" onClick={() => flash('Voice input segera tersedia')}><Mic size={17} /></button><button className="send-button" disabled={!prompt.trim() || isThinking}><ArrowUp size={17} /></button></div></div>{attachments.length > 0 && <div className="attachment-row">{attachments.map((item, index) => <button type="button" key={`${item.name}-${index}`} onClick={() => setAttachments((current) => current.filter((_, itemIndex) => itemIndex !== index))}>📎 {item.name} ×</button>)}</div>}</form>{messages.length === 0 && <div className="suggestion-row"><button onClick={() => setPrompt('Bantu saya memahami workspace ini')}><SquareTerminal size={15} /> Jelajahi workspace</button><button onClick={() => setPrompt('Buatkan rencana kerja untuk hari ini')}><Layers3 size={15} /> Buat rencana</button><button onClick={() => setPrompt('Cari informasi terbaru tentang proyek ini')}><Search size={15} /> Riset sesuatu</button></div>}<p className="composer-note"><Command size={12} /> {notice || activity || 'Astral dapat membaca file, menjalankan tool, dan membantu mengelola workspace.'}</p></div></div></section>
    {permission && <div className="modal-backdrop"><div className="permission-modal"><div className="permission-icon"><ShieldAlert size={22} /></div><p className="eyebrow">PERMISSION REQUIRED</p><h2>Astral meminta izin</h2><p>Astral ingin menjalankan <strong>{permission.tool}</strong>.</p><pre>{JSON.stringify(permission.arguments || {}, null, 2)}</pre><div className="permission-actions"><button className="deny-button" onClick={() => { if (permission.id) bridgeCommand({ type: 'permission_result', id: permission.id, approved: false }); setPermission(null) }}>Tolak</button><button className="save-button" onClick={() => { if (permission.id) bridgeCommand({ type: 'permission_result', id: permission.id, approved: true }); setPermission(null) }}>Izinkan sekali</button></div></div></div>}
    {panel === 'memory' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">LONG-TERM CONTEXT</p><h2>Memory Astral</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div>{memoryDraft ? <><textarea className="settings-textarea" value={memoryDraft.content} onChange={(event) => setMemoryDraft({ ...memoryDraft, content: event.target.value })} /><div className="permission-actions"><button className="deny-button" onClick={() => setMemoryDraft(null)}>Batal</button>{memoryDraft.id && <button className="deny-button" onClick={() => { bridgeCommand({ type: 'memory_delete', id: memoryDraft.id }).catch(() => undefined); setMemoryDraft(null) }}>Hapus</button>}<button className="save-button" onClick={saveMemory}>Simpan</button></div></> : <><div className="memory-list">{memories.length ? memories.map((item) => <button key={item.id} onClick={() => setMemoryDraft(item)}><strong>{item.category || 'general'}</strong><span>{item.content}</span></button>) : <p className="empty-panel">Belum ada memory tersimpan.</p>}</div><button className="save-button" onClick={() => setMemoryDraft({ id: '', content: '', category: 'general', tags: [] })}>+ Tambah memory</button></>}</div></div>}
    {panel === 'settings' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">ASTRAL CONFIGURATION</p><h2>Personalisasi</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><label>Personalization<textarea className="settings-textarea" value={personalization} onChange={(event) => setPersonalization(event.target.value)} placeholder="Contoh: jawab ringkas, panggil saya bos..." /></label><label>System prompt tambahan<textarea className="settings-textarea" value={systemPrompt} onChange={(event) => setSystemPrompt(event.target.value)} placeholder="Instruksi tambahan untuk Astral" /></label><button className="save-button" onClick={saveSettings}>Simpan pengaturan</button></div></div>}
    {panel === 'errors' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">DIAGNOSTICS</p><h2>Error log</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><div className="log-list">{errors.length ? errors.map((error, index) => <article key={error.id || index}><small>{error.time}</small><strong>{error.message}</strong><pre>{error.detail}</pre></article>) : <p className="empty-panel">Belum ada error tercatat.</p>}</div></div></div>}
    {panel === 'apps' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">SYSTEM TOOLS</p><h2>App launcher</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><div className="app-list">{apps.length ? apps.map((app) => <button key={app.app_id || app.name} onClick={() => bridgeCommand({ type: 'app_launch', application: app.name })}><SquareTerminal size={15} /><span>{app.name}</span><small>Launch</small></button>) : <p className="empty-panel">Memuat daftar aplikasi...</p>}</div></div></div>}
  </main>
}

export default App
