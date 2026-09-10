import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Archive, ArrowUp, Check, CheckCheck, ChevronDown, Command, FileCode2, FolderKanban, Gauge, Layers3, Menu, Mic, MoreHorizontal, Plus, RefreshCw, Search, Settings2, Sparkles, Square, SquareTerminal, SunMedium, X } from 'lucide-react'

type Message = { role: 'user' | 'assistant'; text: string; activity?: string }
type BridgeEvent = { type: string; text?: string; name?: string; status?: string; id?: string; session_id?: string; current_session_id?: string; tool?: string; arguments?: Record<string, unknown>; message?: string; detail?: string; provider?: string; items?: any[]; messages?: any[]; settings?: { personalization?: string; system_prompt?: string } }
type Provider = { id: string; label: string; model: string }
type Memory = { id: string; content: string; category?: string; tags?: string[] }
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
  const [reasoning, setReasoning] = useState('')
  const [reasoningOpen, setReasoningOpen] = useState(false)
  const [notice, setNotice] = useState('')
  const [permission, setPermission] = useState<BridgeEvent | null>(null)
  const [provider, setProvider] = useState('local')
  const [modelOpen, setModelOpen] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [lightMode, setLightMode] = useState(false)
  const [history, setHistory] = useState<{ id: string; title: string; updated_at?: string }[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [panel, setPanel] = useState<'memory' | 'settings' | 'errors' | null>(null)
  const [memories, setMemories] = useState<Memory[]>([])
  const [memoryDraft, setMemoryDraft] = useState<Memory | null>(null)
  const [errors, setErrors] = useState<any[]>([])
  const [personalization, setPersonalization] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [lastRequest, setLastRequest] = useState<{ text: string; attachments: Attachment[] } | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const selected = providers.find((item) => item.id === provider) || providers[0]
  const chats: { id: string; title: string; updated_at?: string }[] = history.length ? history : fallbackChats.map((title, index) => ({ id: `demo-${index}`, title }))
  const visibleChats = chats.filter((item) => item.title.toLowerCase().includes(search.toLowerCase()))
  const greeting = useMemo(() => { const hour = new Date().getHours(); return hour < 11 ? 'Selamat pagi, bos.' : hour < 15 ? 'Selamat siang, bos.' : hour < 19 ? 'Selamat sore, bos.' : 'Selamat malam, bos.' }, [])
  const bridgeCommand = (command: Record<string, unknown>) => invoke('bridge_command', { command })
  const flash = (text: string) => { setNotice(text); window.setTimeout(() => setNotice(''), 2400) }

  useEffect(() => {
    if (!('__TAURI_INTERNALS__' in window)) return
    invoke<boolean>('bridge_status').then(setBridgeReady).catch(() => setBridgeReady(false))
    const unlisten = listen<BridgeEvent>('astral-event', ({ payload }) => {
      if (payload.type === 'bridge_ready' || payload.type === 'provider_changed') { setBridgeReady(true); if (payload.provider) setProvider(payload.provider); if (payload.session_id) setCurrentSessionId(payload.session_id) }
      if (payload.type === 'thinking') setActivity(payload.status || 'working...')
      if (payload.type === 'thinking_end') setActivity('')
      if (payload.type === 'tool_start') setActivity(`Running ${payload.name || 'tool'}...`)
      if (payload.type === 'tool_complete') setActivity('')
      if (payload.type === 'reasoning_start') { setReasoning(''); setReasoningOpen(false) }
      if (payload.type === 'reasoning_token') setReasoning((current) => current + (payload.text || ''))
      if (payload.type === 'permission_required') { setPermission(payload); setActivity(`Permission diperlukan untuk ${payload.tool || 'tool'}`) }
      if (payload.type === 'response_start') setMessages((current) => current.at(-1)?.role === 'assistant' && current.at(-1)?.text === '' ? current : [...current, { role: 'assistant', text: '' }])
      if (payload.type === 'token') setMessages((current) => { const next = [...current]; const last = next.at(-1); if (!last || last.role !== 'assistant') next.push({ role: 'assistant', text: payload.text || '' }); else last.text += payload.text || ''; return next })
      if (payload.type === 'complete') { if (payload.session_id) setCurrentSessionId(payload.session_id); setMessages((current) => { const next = [...current]; const last = next.at(-1); if (last?.role === 'assistant') last.text = payload.text || last.text; else if (payload.text) next.push({ role: 'assistant', text: payload.text }); return next }) }
      if (payload.type === 'request_cancelled') { setIsThinking(false); setPermission(null); setActivity('Response dihentikan') }
      if (['complete', 'response_end'].includes(payload.type)) { setIsThinking(false); setActivity(''); setPermission(null) }
      if (payload.type === 'session_reset') { setMessages([]); setCurrentSessionId(payload.session_id || null); setIsThinking(false); setPermission(null) }
      if (payload.type === 'error') { setErrors((current) => [{ message: payload.message, detail: payload.detail, time: new Date().toISOString() }, ...current]); setMessages((current) => [...current, { role: 'assistant', text: `${payload.message || 'Terjadi kesalahan.'}${payload.detail ? `\n\n${payload.detail}` : ''}` }]); setIsThinking(false); setActivity(''); setPermission(null) }
      if (payload.type === 'history_list') { setHistory(payload.items || []); if (payload.current_session_id) setCurrentSessionId(payload.current_session_id) }
      if (payload.type === 'history_loaded') { setCurrentSessionId(payload.id || null); setMessages((payload.messages || []).map((item: any) => ({ role: item.role, text: item.text ?? item.content ?? '' })) as Message[]) }
      if (['memory_list', 'memory_saved', 'memory_deleted'].includes(payload.type)) setMemories(payload.items || [])
      if (payload.type === 'settings') { setPersonalization(payload.settings?.personalization || ''); setSystemPrompt(payload.settings?.system_prompt || '') }
      if (payload.type === 'error_log') setErrors(payload.items || [])
    })
    bridgeCommand({ type: 'history_list' }).catch(() => undefined)
    bridgeCommand({ type: 'settings_get' }).catch(() => undefined)
    return () => { unlisten.then((stop) => stop()) }
  }, [])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, activity, reasoning, permission])

  function submit(event: FormEvent) {
    event.preventDefault(); const text = prompt.trim()
    if ((!text && attachments.length === 0) || isThinking) return
    const requestAttachments = [...attachments]
    setLastRequest({ text, attachments: requestAttachments }); setMessages((current) => [...current, { role: 'user', text: text || 'Image terlampir' }]); setPrompt(''); setAttachments([]); setIsThinking(true); setReasoning('')
    if (bridgeReady) bridgeCommand({ type: 'user_message', text, attachments: requestAttachments }).catch((error) => { flash(String(error)); setIsThinking(false) })
    else window.setTimeout(() => { setMessages((current) => [...current, { role: 'assistant', text: 'Jalankan Astral melalui Tauri untuk menghubungkan Agent Python.', activity: 'Tauri bridge belum aktif' }]); setIsThinking(false) }, 500)
  }
  function retryRequest() { if (!lastRequest || isThinking) return; setMessages((current) => [...current, { role: 'user', text: lastRequest.text || 'Image terlampir' }]); setIsThinking(true); setActivity('Retrying response...'); bridgeCommand({ type: 'user_message', text: lastRequest.text, attachments: lastRequest.attachments }).catch((error) => { flash(String(error)); setIsThinking(false) }) }
  function stopResponse() { bridgeCommand({ type: 'cancel_request' }).catch(() => undefined); setActivity('Stopping...') }
  function openExternal(url?: string) { if (!url) return; invoke('open_external', { url }).catch((error) => flash(String(error))) }
  function openPanel(name: 'memory' | 'settings' | 'errors') { setPanel(name); bridgeCommand({ type: { memory: 'memory_list', settings: 'settings_get', errors: 'error_log' }[name] }).catch(() => undefined) }
  function insertFiles(files: FileList | null) { if (!files) return; Array.from(files).forEach((file) => { if (file.type.startsWith('image/')) { const reader = new FileReader(); reader.onload = () => setAttachments((current) => [...current, { name: file.name, kind: 'screenshot', content: String(reader.result) }]); reader.readAsDataURL(file) } else file.text().then((content) => setAttachments((current) => [...current, { name: file.name, kind: 'file', content: content.slice(0, 12000) }])) }) }
  function saveSettings() { bridgeCommand({ type: 'settings_save', personalization, system_prompt: systemPrompt }).catch(() => undefined); setPanel(null) }
  function saveMemory() { if (memoryDraft?.content.trim()) bridgeCommand({ type: 'memory_save', id: memoryDraft.id, content: memoryDraft.content, category: memoryDraft.category || 'general', tags: memoryDraft.tags || [] }).catch(() => undefined); setMemoryDraft(null) }
  function permissionResult(approved: boolean, always = false) { if (permission?.id) bridgeCommand({ type: 'permission_result', id: permission.id, approved, always }).catch(() => undefined); setPermission(null); if (!approved) setActivity('Permission ditolak') }

  return <main className={`app-shell ${lightMode ? 'app-shell--light' : ''}`}>
    <aside className={`sidebar ${sidebarOpen ? '' : 'sidebar--closed'}`}>
      <div className="sidebar-topbar"><button className="brand-lockup" onClick={() => setSidebarOpen(true)}><span className="astral-mark"><Sparkles size={16} /></span><span className="brand-name">ASTRAL</span></button><button className="icon-button subtle" onClick={() => setSidebarOpen(false)}><X size={17} /></button></div>
      <div className="sidebar-actions"><button className="new-chat" onClick={() => { setMessages([]); setCurrentSessionId(null); bridgeCommand({ type: 'new_chat' }).catch(() => undefined) }}><Plus size={16} /> New chat</button>{searchOpen ? <div className="search-field"><Search size={15} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari..." /><button onClick={() => { setSearchOpen(false); setSearch('') }}><X size={13} /></button></div> : <button className="nav-item" onClick={() => setSearchOpen(true)}><Search size={16} /> Cari percakapan <kbd>Ctrl K</kbd></button>}</div>
      <div className="sidebar-section"><div className="section-label"><span>Percakapan</span><MoreHorizontal size={16} /></div><div className="conversation-list">{visibleChats.map((chat) => <button className={`conversation ${chat.id === currentSessionId ? 'conversation--active' : ''}`} key={chat.id} onClick={() => chat.id.startsWith('demo-') ? flash(chat.title) : bridgeCommand({ type: 'history_load', id: chat.id })}><span className="conversation-dot" /><span className="conversation-copy"><strong>{chat.title}</strong><small>{chat.updated_at ? 'Tersimpan' : 'Demo'}</small></span></button>)}</div></div>
      <div className="sidebar-section sidebar-section--lower"><div className="section-label"><span>Workspace</span></div><button className="nav-item" onClick={() => flash('File browser akan terhubung ke workspace')}><FolderKanban size={16} /> Files</button><button className="nav-item" onClick={() => openPanel('memory')}><Archive size={16} /> Memory</button><button className="nav-item" onClick={() => openPanel('errors')}><Gauge size={16} /> Error log</button></div>
      <div className="sidebar-footer"><button className="profile-button" onClick={() => openPanel('settings')}><span className="avatar">A</span><span><strong>astral</strong><small>Local workspace</small></span><ChevronDown size={15} /></button><button className="icon-button subtle" onClick={() => openPanel('settings')}><Settings2 size={17} /></button></div>
    </aside>

    <section className="main-panel"><header className="topbar">{!sidebarOpen && <button className="icon-button" onClick={() => setSidebarOpen(true)}><Menu size={18} /></button>}<div className="topbar-context"><span className="status-dot" /> Local agent <span className="slash">/</span> <span className="muted">Workspace</span></div><div className="topbar-actions"><button className="icon-button" onClick={() => setLightMode((value) => !value)} title="Toggle light mode"><SunMedium size={17} /></button><div className="more-wrap"><button className="icon-button" onClick={() => setMoreOpen((value) => !value)}><MoreHorizontal size={18} /></button>{moreOpen && <div className="popover top-popover"><button onClick={() => openPanel('errors')}>Error log</button><button onClick={() => openPanel('settings')}>Settings</button></div>}</div></div></header>
      <div className={`chat-area ${messages.length ? 'chat-area--active' : ''}`}>
        {messages.length === 0 ? <div className="welcome-state"><div className="welcome-orb"><Sparkles size={30} /></div><p className="eyebrow">LOCAL-FIRST · READY TO HELP</p><h1>{greeting}</h1><p className="welcome-copy">Apa yang ingin kamu kerjakan hari ini?</p></div> : <div className="message-stack">
          {messages.map((message, index) => <article className={`message message--${message.role}`} key={`${message.role}-${index}`}><div className="message-avatar">{message.role === 'user' ? 'A' : <Sparkles size={15} />}</div><div className="message-body"><div className="message-meta">{message.role === 'user' ? 'Kamu' : 'Astral'}</div>{message.role === 'assistant' ? <div className="markdown-content"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: ({ href, children, ...props }) => <a {...props} href={href} target="_blank" rel="noreferrer" onClick={(event) => { event.preventDefault(); openExternal(href) }}>{children}</a> }}>{message.text}</ReactMarkdown></div> : <p>{message.text}</p>}{message.activity && <div className="activity-pill"><span className="activity-pulse" />{message.activity}</div>}</div></article>)}
          {isThinking && <div className="thinking-row"><span className="thinking-mark"><Sparkles size={15} /></span><span className="thinking-dots"><i /><i /><i /></span><span>{activity || 'working...'}</span></div>}
          {reasoning && <div className="reasoning-card"><button className="reasoning-toggle" onClick={() => setReasoningOpen((value) => !value)}><span className="reasoning-icon"><Sparkles size={13} /></span><span>{reasoningOpen ? 'Hide reasoning' : 'View reasoning'}</span><ChevronDown size={14} className={reasoningOpen ? 'reasoning-chevron reasoning-chevron--open' : 'reasoning-chevron'} /></button>{reasoningOpen && <div className="reasoning-content">{reasoning}</div>}</div>}
          {permission && <div className="permission-inline"><div><strong>Permission diperlukan</strong><small>{permission.tool} · pilih tindakan untuk melanjutkan</small></div><div className="permission-inline-actions"><button className="permission-deny" title="Deny" onClick={() => permissionResult(false)}><X size={16} /></button><button className="permission-allow" title="Allow once" onClick={() => permissionResult(true)}><Check size={16} /></button><button className="permission-always" title="Always allow this tool" onClick={() => permissionResult(true, true)}><CheckCheck size={17} /></button></div></div>}
          <div ref={messagesEndRef} />
        </div>}

        <div className="composer-wrap">{attachments.length > 0 && <div className="attachment-preview-row">{attachments.map((item, index) => <div className="attachment-preview" key={`${item.name}-${index}`}>{item.kind === 'screenshot' && item.content ? <img src={item.content} alt={item.name} /> : <FileCode2 size={18} />}<span title={item.name}>{item.name}</span><button type="button" onClick={() => setAttachments((current) => current.filter((_, itemIndex) => itemIndex !== index))}><X size={12} /></button></div>)}</div>}
          <form className="composer" onSubmit={submit}><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} onPaste={(event) => { if (event.clipboardData.files.length) { event.preventDefault(); insertFiles(event.clipboardData.files) } }} placeholder="Tulis pesan untuk Astral..." rows={1} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(event) } }} /><div className="composer-bottom"><div className="composer-tools"><button type="button" className="round-tool" onClick={() => fileInput.current?.click()}><Plus size={18} /></button><button type="button" className="tool-chip" onClick={() => fileInput.current?.click()}><FileCode2 size={15} /> Insert file</button>{lastRequest && !isThinking && <button type="button" className="tool-chip" onClick={retryRequest}><RefreshCw size={14} /> Retry</button>}<input ref={fileInput} hidden type="file" multiple onChange={(event) => { insertFiles(event.target.files); event.currentTarget.value = '' }} /></div><div className="composer-model"><div className="model-wrap"><button type="button" className="model-picker" onClick={() => setModelOpen((value) => !value)}>{selected.label}<ChevronDown size={14} /></button>{modelOpen && <div className="popover model-popover">{providers.map((item) => <button type="button" key={item.id} className={item.id === provider ? 'selected' : ''} onClick={() => { setProvider(item.id); setModelOpen(false); bridgeCommand({ type: 'set_provider', provider: item.id }).catch(() => undefined) }}><span><strong>{item.label}</strong><small>{item.model}</small></span>{item.id === provider && <span className="check">✓</span>}</button>)}</div>}</div><button type="button" className="round-tool" onClick={() => flash('Voice input segera tersedia')}><Mic size={17} /></button>{isThinking ? <button type="button" className="send-button stop-button" title="Stop response" onClick={stopResponse}><Square size={15} /></button> : <button className="send-button" disabled={!prompt.trim() && attachments.length === 0}><ArrowUp size={17} /></button>}</div></div></form>
          {messages.length === 0 && <div className="suggestion-row"><button onClick={() => setPrompt('Bantu saya memahami workspace ini')}><SquareTerminal size={15} /> Jelajahi workspace</button><button onClick={() => setPrompt('Buatkan rencana kerja untuk hari ini')}><Layers3 size={15} /> Buat rencana</button><button onClick={() => setPrompt('Cari informasi terbaru tentang proyek ini')}><Search size={15} /> Riset sesuatu</button></div>}<p className="composer-note"><Command size={12} /> {notice || activity || 'Astral dapat membaca file, menjalankan tool, dan membantu mengelola workspace.'}</p>
        </div>
      </div>
    </section>

    {panel === 'memory' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">LONG-TERM CONTEXT</p><h2>Memory Astral</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div>{memoryDraft ? <><textarea className="settings-textarea" value={memoryDraft.content} onChange={(event) => setMemoryDraft({ ...memoryDraft, content: event.target.value })} /><div className="permission-actions"><button className="deny-button" onClick={() => setMemoryDraft(null)}>Batal</button>{memoryDraft.id && <button className="deny-button" onClick={() => { bridgeCommand({ type: 'memory_delete', id: memoryDraft.id }).catch(() => undefined); setMemoryDraft(null) }}>Hapus</button>}<button className="save-button" onClick={saveMemory}>Simpan</button></div></> : <><div className="memory-list">{memories.length ? memories.map((item) => <button key={item.id} onClick={() => setMemoryDraft(item)}><strong>{item.category || 'general'}</strong><span>{item.content}</span></button>) : <p className="empty-panel">Belum ada memory tersimpan.</p>}</div><button className="save-button" onClick={() => setMemoryDraft({ id: '', content: '', category: 'general', tags: [] })}>+ Tambah memory</button></>}</div></div>}
    {panel === 'settings' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">ASTRAL CONFIGURATION</p><h2>Personalisasi & system prompt</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><label>Personalization<textarea className="settings-textarea" value={personalization} onChange={(event) => setPersonalization(event.target.value)} placeholder="Contoh: jawab ringkas, panggil saya bos..." /></label><label>System prompt utama<textarea className="settings-textarea system-prompt-editor" value={systemPrompt} onChange={(event) => setSystemPrompt(event.target.value)} placeholder="System prompt Astral" /></label><button className="save-button" onClick={saveSettings}>Simpan pengaturan</button></div></div>}
    {panel === 'errors' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">DIAGNOSTICS</p><h2>Error log</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><div className="log-list">{errors.length ? errors.map((error, index) => <article key={error.id || index}><small>{error.time}</small><strong>{error.message}</strong><pre>{error.detail}</pre></article>) : <p className="empty-panel">Belum ada error tercatat.</p>}</div></div></div>}
  </main>
}

export default App
