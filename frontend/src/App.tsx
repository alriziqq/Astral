import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Archive, ArrowUp, CalendarClock, Check, CheckCheck, ChevronDown, Command, FileCode2, FolderKanban, Gauge, Layers3, Menu, Mic, MoreHorizontal, Plus, RefreshCw, Search, Settings2, Square, SquareTerminal, SunMedium, Trash2, X } from 'lucide-react'

type Message = { role: 'user' | 'assistant'; text: string; activity?: string }
type BridgeEvent = { type: string; text?: string; name?: string; status?: string; id?: string; session_id?: string; current_session_id?: string; tool?: string; arguments?: Record<string, unknown>; message?: string; detail?: string; provider?: string; items?: any[]; messages?: any[]; settings?: { personalization?: string; system_prompt?: string; brief_enabled?: boolean; brief_morning?: string; brief_evening?: string; brief_location?: string; voice_standby?: boolean; voice_tts?: boolean } }
type Provider = { id: string; label: string; model: string }
type Memory = { id: string; content: string; category?: string; tags?: string[] }
type Attachment = { name: string; kind: 'file' | 'screenshot'; content?: string }

function AstralMark({ size = 24, className }: { size?: number; className?: string }) {
  return <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2.8c0 5.2 1.6 7.8 8.8 9.2-7.2 1.4-8.8 4-8.8 9.2 0-5.2-1.6-7.8-8.8-9.2C10.4 10.6 12 8 12 2.8Z" />
      <path d="M3.8 5.2c3.1 1.6 5.1 3.7 6.1 6.8-1 3.1-3 5.2-6.1 6.8 3.1-1.6 5.1-3.7 6.1-6.8-1-3.1-3-5.2-6.1-6.8Z" opacity=".72" />
    </g>
    <circle cx="12" cy="12" r="1.35" fill="currentColor" />
  </svg>
}

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
  const [pendingDelete, setPendingDelete] = useState<{ id: string; title: string } | null>(null)
  const [panel, setPanel] = useState<'memory' | 'settings' | 'errors' | null>(null)
  const [memories, setMemories] = useState<Memory[]>([])
  const [memoryDraft, setMemoryDraft] = useState<Memory | null>(null)
  const [errors, setErrors] = useState<any[]>([])
  const [personalization, setPersonalization] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [briefEnabled, setBriefEnabled] = useState(true)
  const [briefMorning, setBriefMorning] = useState('08:00')
  const [briefEvening, setBriefEvening] = useState('20:00')
  const [briefLocation, setBriefLocation] = useState('Riau')
  const [voiceListening, setVoiceListening] = useState(false)
  const [voiceStandby, setVoiceStandby] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const recognitionRef = useRef<any>(null)
  const voiceListeningRef = useRef(false)
  const spokenMessageRef = useRef('')
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
      if (payload.type === 'history_deleted') { setHistory(payload.items || []); if (payload.current_session_id) setCurrentSessionId(payload.current_session_id) }
      if (payload.type === 'history_delete_error') flash(payload.message || 'History gagal dihapus.')
      if (payload.type === 'history_loaded') { setCurrentSessionId(payload.id || null); setMessages((payload.messages || []).map((item: any) => ({ role: item.role, text: item.text ?? item.content ?? '' })) as Message[]) }
      if (['memory_list', 'memory_saved', 'memory_deleted'].includes(payload.type)) setMemories(payload.items || [])
      if (payload.type === 'settings') { setPersonalization(payload.settings?.personalization || ''); setSystemPrompt(payload.settings?.system_prompt || '') }
      if (payload.type === 'settings') { setBriefEnabled(payload.settings?.brief_enabled ?? true); setBriefMorning(payload.settings?.brief_morning || '08:00'); setBriefEvening(payload.settings?.brief_evening || '20:00'); setBriefLocation(payload.settings?.brief_location || 'Riau'); setVoiceStandby(payload.settings?.voice_standby ?? false); setTtsEnabled(payload.settings?.voice_tts ?? false) }
      if (payload.type === 'scheduled_brief') { setMessages((current) => [...current, { role: 'assistant', text: payload.text || '' }]); setActivity('') }
      if (payload.type === 'error_log') setErrors(payload.items || [])
    })
    bridgeCommand({ type: 'history_list' }).catch(() => undefined)
    bridgeCommand({ type: 'settings_get' }).catch(() => undefined)
    return () => { unlisten.then((stop) => stop()) }
  }, [])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, activity, reasoning, permission])

  useEffect(() => {
    if (!ttsEnabled || isThinking || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') return
    const last = messages.at(-1)
    if (!last || last.role !== 'assistant' || !last.text.trim() || last.text === spokenMessageRef.current) return
    const clean = last.text.replace(/```[\s\S]*?```/g, '').replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[*_#>`~-]/g, '').replace(/\s+/g, ' ').trim()
    if (!clean) return
    const words = clean.split(' ').slice(0, 8)
    while (words.length < 3) words.push('sudah selesai')
    const summary = words.slice(0, 8).join(' ')
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(summary)
    utterance.lang = 'id-ID'; utterance.rate = .96; utterance.pitch = .98
    window.speechSynthesis.speak(utterance)
    spokenMessageRef.current = last.text
  }, [messages, isThinking, ttsEnabled])

  useEffect(() => () => { voiceListeningRef.current = false; recognitionRef.current?.stop(); window.speechSynthesis?.cancel() }, [])

  function stopVoice() {
    voiceListeningRef.current = false
    recognitionRef.current?.stop()
    recognitionRef.current = null
    setVoiceListening(false)
    setActivity('')
  }

  function startVoice() {
    const browserWindow = window as Window & { SpeechRecognition?: any; webkitSpeechRecognition?: any }
    const Recognition = browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition
    if (!Recognition) { flash('Voice input membutuhkan Web Speech API pada WebView ini.'); return }
    if (voiceListeningRef.current) return
    const recognition = new Recognition()
    recognition.continuous = true; recognition.interimResults = false; recognition.lang = 'id-ID'
    recognition.onstart = () => { voiceListeningRef.current = true; setVoiceListening(true); setActivity('Mendengarkan...') }
    recognition.onerror = (event: any) => { if (event.error !== 'no-speech' && event.error !== 'aborted') flash(`Voice input: ${event.error}`) }
    recognition.onend = () => { if (voiceListeningRef.current) window.setTimeout(() => { try { recognition.start() } catch { /* already restarting */ } }, 180) }
    recognition.onresult = (event: any) => {
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        if (!event.results[index].isFinal) continue
        const transcript = String(event.results[index][0]?.transcript || '').trim()
        if (!transcript) continue
        setPrompt((current) => `${current} ${transcript}`.trim())
      }
    }
    recognitionRef.current = recognition
    voiceListeningRef.current = true
    try { recognition.start() } catch { voiceListeningRef.current = false; setVoiceListening(false); flash('Mikrofon belum dapat diaktifkan.') }
  }

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
  function saveSettings() { bridgeCommand({ type: 'settings_save', personalization, system_prompt: systemPrompt, brief_enabled: briefEnabled, brief_morning: briefMorning, brief_evening: briefEvening, brief_location: briefLocation, voice_standby: voiceStandby, voice_tts: ttsEnabled }).catch(() => undefined); setPanel(null) }
  function requestBrief() { setActivity('Menyusun work brief...'); bridgeCommand({ type: 'work_brief' }).catch((error) => { setActivity(''); flash(String(error)) }) }
  function saveMemory() { if (memoryDraft?.content.trim()) bridgeCommand({ type: 'memory_save', id: memoryDraft.id, content: memoryDraft.content, category: memoryDraft.category || 'general', tags: memoryDraft.tags || [] }).catch(() => undefined); setMemoryDraft(null) }
  function deleteHistory(chat: { id: string; title: string }) {
    if (chat.id.startsWith('demo-')) { flash('Percakapan demo tidak dapat dihapus'); return }
    setPendingDelete(chat)
  }
  function confirmDeleteHistory() {
    if (!pendingDelete) return
    bridgeCommand({ type: 'history_delete', id: pendingDelete.id }).then(() => window.setTimeout(() => { bridgeCommand({ type: 'history_list' }).catch(() => undefined) }, 120)).catch((error) => flash(String(error)))
    setPendingDelete(null)
  }
  function permissionResult(approved: boolean, always = false) { if (permission?.id) bridgeCommand({ type: 'permission_result', id: permission.id, approved, always }).catch(() => undefined); setPermission(null); if (!approved) setActivity('Permission ditolak') }

  return <main className={`app-shell ${lightMode ? 'app-shell--light' : ''}`}>
    <aside className={`sidebar ${sidebarOpen ? '' : 'sidebar--closed'}`}>
      <div className="sidebar-topbar"><button className="brand-lockup" onClick={() => setSidebarOpen(true)}><span className="astral-mark"><AstralMark size={25} /></span><span className="brand-name">ASTRAL</span></button><button className="icon-button subtle" onClick={() => setSidebarOpen(false)}><X size={17} /></button></div>
      <div className="sidebar-actions"><button className="new-chat" onClick={() => { setMessages([]); setCurrentSessionId(null); bridgeCommand({ type: 'new_chat' }).catch(() => undefined) }}><Plus size={16} /> New chat</button>{searchOpen ? <div className="search-field"><Search size={15} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari..." /><button onClick={() => { setSearchOpen(false); setSearch('') }}><X size={13} /></button></div> : <button className="nav-item" onClick={() => setSearchOpen(true)}><Search size={16} /> Cari percakapan <kbd>Ctrl K</kbd></button>}</div>
      <div className="sidebar-section"><div className="section-label"><span>Percakapan</span><MoreHorizontal size={16} /></div><div className="conversation-list">{visibleChats.map((chat) => <div className="conversation-row" key={chat.id}><button className={`conversation ${chat.id === currentSessionId ? 'conversation--active' : ''}`} onClick={() => chat.id.startsWith('demo-') ? flash(chat.title) : bridgeCommand({ type: 'history_load', id: chat.id })}><span className="conversation-dot" /><span className="conversation-copy"><strong>{chat.title}</strong><small>{chat.updated_at ? 'Tersimpan' : 'Demo'}</small></span></button>{!chat.id.startsWith('demo-') && <button className="conversation-delete" title={`Hapus ${chat.title}`} aria-label={`Hapus ${chat.title}`} onClick={() => deleteHistory(chat)}><Trash2 size={14} /></button>}</div>)}</div></div>
      <div className="sidebar-section sidebar-section--lower"><div className="section-label"><span>Workspace</span></div><button className="nav-item" onClick={() => flash('File browser akan terhubung ke workspace')}><FolderKanban size={16} /> Files</button><button className="nav-item" onClick={() => openPanel('memory')}><Archive size={16} /> Memory</button><button className="nav-item" onClick={() => openPanel('errors')}><Gauge size={16} /> Error log</button></div>
      <div className="sidebar-footer"><button className="profile-button" onClick={() => openPanel('settings')}><span className="avatar">A</span><span><strong>astral</strong><small>Local workspace</small></span><ChevronDown size={15} /></button><button className="icon-button subtle" onClick={() => openPanel('settings')}><Settings2 size={17} /></button></div>
    </aside>

    <section className="main-panel"><header className="topbar">{!sidebarOpen && <button className="icon-button" onClick={() => setSidebarOpen(true)}><Menu size={18} /></button>}<div className="topbar-context"><span className="status-dot" /> Local agent <span className="slash">/</span> <span className="muted">Workspace</span></div><div className="topbar-actions"><button className="icon-button" onClick={() => setLightMode((value) => !value)} title="Toggle light mode"><SunMedium size={17} /></button><div className="more-wrap"><button className="icon-button" onClick={() => setMoreOpen((value) => !value)}><MoreHorizontal size={18} /></button>{moreOpen && <div className="popover top-popover"><button onClick={() => openPanel('errors')}>Error log</button><button onClick={() => openPanel('settings')}>Settings</button></div>}</div></div></header>
      <div className={`chat-area ${messages.length ? 'chat-area--active' : ''}`}>
        {messages.length === 0 ? <div className="welcome-state"><div className="welcome-orb"><AstralMark size={44} /></div><p className="eyebrow">LOCAL-FIRST · READY TO HELP</p><h1>{greeting}</h1><p className="welcome-copy">Apa yang ingin kamu kerjakan hari ini?</p></div> : <div className="message-stack">
          {messages.map((message, index) => <article className={`message message--${message.role}`} key={`${message.role}-${index}`}><div className="message-avatar">{message.role === 'user' ? 'A' : <AstralMark size={17} />}</div><div className="message-body"><div className="message-meta">{message.role === 'user' ? 'Kamu' : 'Astral'}</div>{message.role === 'assistant' ? <div className="markdown-content"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: ({ href, children, ...props }) => <a {...props} href={href} target="_blank" rel="noreferrer" onClick={(event) => { event.preventDefault(); openExternal(href) }}>{children}</a> }}>{message.text}</ReactMarkdown></div> : <p>{message.text}</p>}{message.activity && <div className="activity-pill"><span className="activity-pulse" />{message.activity}</div>}</div></article>)}
          {isThinking && <div className="thinking-row"><span className="thinking-mark"><AstralMark size={17} /></span><span className="thinking-dots"><i /><i /><i /></span><span>{activity || 'working...'}</span></div>}
          {reasoning && <div className="reasoning-card"><button className="reasoning-toggle" onClick={() => setReasoningOpen((value) => !value)}><span className="reasoning-icon"><AstralMark size={15} /></span><span>{reasoningOpen ? 'Hide reasoning' : 'View reasoning'}</span><ChevronDown size={14} className={reasoningOpen ? 'reasoning-chevron reasoning-chevron--open' : 'reasoning-chevron'} /></button>{reasoningOpen && <div className="reasoning-content">{reasoning}</div>}</div>}
          {permission && <div className="permission-inline"><div><strong>Permission diperlukan</strong><small>{permission.tool} · pilih tindakan untuk melanjutkan</small></div><div className="permission-inline-actions"><button className="permission-deny" title="Deny" onClick={() => permissionResult(false)}><X size={16} /></button><button className="permission-allow" title="Allow once" onClick={() => permissionResult(true)}><Check size={16} /></button><button className="permission-always" title="Always allow this tool" onClick={() => permissionResult(true, true)}><CheckCheck size={17} /></button></div></div>}
          <div ref={messagesEndRef} />
        </div>}

        <div className="composer-wrap">{attachments.length > 0 && <div className="attachment-preview-row">{attachments.map((item, index) => <div className="attachment-preview" key={`${item.name}-${index}`}>{item.kind === 'screenshot' && item.content ? <img src={item.content} alt={item.name} /> : <FileCode2 size={18} />}<span title={item.name}>{item.name}</span><button type="button" onClick={() => setAttachments((current) => current.filter((_, itemIndex) => itemIndex !== index))}><X size={12} /></button></div>)}</div>}
          <form className="composer" onSubmit={submit}><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} onPaste={(event) => { if (event.clipboardData.files.length) { event.preventDefault(); insertFiles(event.clipboardData.files) } }} placeholder="Tulis pesan untuk Astral..." rows={1} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(event) } }} /><div className="composer-bottom"><div className="composer-tools"><button type="button" className="round-tool" onClick={() => fileInput.current?.click()}><Plus size={18} /></button><button type="button" className="tool-chip" onClick={() => fileInput.current?.click()}><FileCode2 size={15} /> Insert file</button>{lastRequest && !isThinking && <button type="button" className="tool-chip" onClick={retryRequest}><RefreshCw size={14} /> Retry</button>}<input ref={fileInput} hidden type="file" multiple onChange={(event) => { insertFiles(event.target.files); event.currentTarget.value = '' }} /></div><div className="composer-model"><div className="model-wrap"><button type="button" className="model-picker" onClick={() => setModelOpen((value) => !value)}>{selected.label}<ChevronDown size={14} /></button>{modelOpen && <div className="popover model-popover">{providers.map((item) => <button type="button" key={item.id} className={item.id === provider ? 'selected' : ''} onClick={() => { setProvider(item.id); setModelOpen(false); bridgeCommand({ type: 'set_provider', provider: item.id }).catch(() => undefined) }}><span><strong>{item.label}</strong><small>{item.model}</small></span>{item.id === provider && <span className="check">✓</span>}</button>)}</div>}</div><button type="button" className={`round-tool ${voiceListening ? 'round-tool--listening' : ''}`} title={voiceListening ? 'Stop voice input' : 'Start voice input'} onClick={() => voiceListening ? stopVoice() : startVoice()}><Mic size={17} /></button>{isThinking ? <button type="button" className="send-button stop-button" title="Stop response" onClick={stopResponse}><Square size={15} /></button> : <button className="send-button" disabled={!prompt.trim() && attachments.length === 0}><ArrowUp size={17} /></button>}</div></div></form>
          <div className="suggestion-row">{messages.length === 0 && <><button onClick={() => setPrompt('Bantu saya memahami workspace ini')}><SquareTerminal size={15} /> Jelajahi workspace</button><button onClick={() => setPrompt('Buatkan rencana kerja untuk hari ini')}><Layers3 size={15} /> Buat rencana</button><button onClick={() => setPrompt('Cari informasi terbaru tentang proyek ini')}><Search size={15} /> Riset sesuatu</button></>}<button className="brief-shortcut" onClick={requestBrief}><CalendarClock size={15} /> Work brief</button></div><p className="composer-note"><Command size={12} /> {notice || activity || 'Astral dapat membaca file, menjalankan tool, dan membantu mengelola workspace.'}</p>
        </div>
      </div>
    </section>

    {panel === 'memory' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">LONG-TERM CONTEXT</p><h2>Memory Astral</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div>{memoryDraft ? <><textarea className="settings-textarea" value={memoryDraft.content} onChange={(event) => setMemoryDraft({ ...memoryDraft, content: event.target.value })} /><div className="permission-actions"><button className="deny-button" onClick={() => setMemoryDraft(null)}>Batal</button>{memoryDraft.id && <button className="deny-button" onClick={() => { bridgeCommand({ type: 'memory_delete', id: memoryDraft.id }).catch(() => undefined); setMemoryDraft(null) }}>Hapus</button>}<button className="save-button" onClick={saveMemory}>Simpan</button></div></> : <><div className="memory-list">{memories.length ? memories.map((item) => <button key={item.id} onClick={() => setMemoryDraft(item)}><strong>{item.category || 'general'}</strong><span>{item.content}</span></button>) : <p className="empty-panel">Belum ada memory tersimpan.</p>}</div><button className="save-button" onClick={() => setMemoryDraft({ id: '', content: '', category: 'general', tags: [] })}>+ Tambah memory</button></>}</div></div>}
    {panel === 'settings' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">ASTRAL CONFIGURATION</p><h2>Personalisasi & system prompt</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><label>Personalization<textarea className="settings-textarea" value={personalization} onChange={(event) => setPersonalization(event.target.value)} placeholder="Contoh: jawab ringkas, panggil saya bos..." /></label><label>System prompt utama<textarea className="settings-textarea system-prompt-editor" value={systemPrompt} onChange={(event) => setSystemPrompt(event.target.value)} placeholder="System prompt Astral" /></label><div className="brief-settings"><div className="brief-settings-heading"><div><strong>Scheduled work brief</strong><small>Todo, cuaca, dan berita singkat otomatis saat Astral aktif.</small></div><label className="switch"><input type="checkbox" checked={briefEnabled} onChange={(event) => setBriefEnabled(event.target.checked)} /><span /></label></div><div className="brief-settings-grid"><label>Lokasi cuaca<input value={briefLocation} onChange={(event) => setBriefLocation(event.target.value)} placeholder="Riau" /></label><label>Brief pagi<input type="time" value={briefMorning} onChange={(event) => setBriefMorning(event.target.value)} /></label><label>Brief malam<input type="time" value={briefEvening} onChange={(event) => setBriefEvening(event.target.value)} /></label></div><p className="brief-settings-note">Jadwal menggunakan waktu lokal perangkat. Gunakan tombol Work brief untuk menjalankan manual.</p></div><div className="voice-settings"><div><strong>Voice mode</strong><small>Tekan tombol mikrofon untuk mulai merekam perintah secara langsung.</small></div><label className="setting-check"><input type="checkbox" checked={voiceStandby} onChange={(event) => { setVoiceStandby(event.target.checked); if (event.target.checked && !voiceListening) startVoice(); if (!event.target.checked && voiceListening) stopVoice() }} /><span>Standby microphone</span></label><label className="setting-check"><input type="checkbox" checked={ttsEnabled} onChange={(event) => setTtsEnabled(event.target.checked)} /><span>TTS ringkas (3–8 kata)</span></label></div><button className="save-button" onClick={saveSettings}>Simpan pengaturan</button></div></div>}
    {panel === 'errors' && <div className="modal-backdrop" onClick={() => setPanel(null)}><div className="settings-modal wide-modal" onClick={(event) => event.stopPropagation()}><div className="modal-heading"><div><p className="eyebrow">DIAGNOSTICS</p><h2>Error log</h2></div><button className="icon-button" onClick={() => setPanel(null)}><X size={18} /></button></div><div className="log-list">{errors.length ? errors.map((error, index) => <article key={error.id || index}><small>{error.time}</small><strong>{error.message}</strong><pre>{error.detail}</pre></article>) : <p className="empty-panel">Belum ada error tercatat.</p>}</div></div></div>}
    {pendingDelete && <div className="modal-backdrop" onClick={() => setPendingDelete(null)}><div className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-history-title" onClick={(event) => event.stopPropagation()}><div className="confirm-icon"><Trash2 size={19} /></div><p className="eyebrow">DELETE CONVERSATION</p><h2 id="delete-history-title">Hapus percakapan ini?</h2><p className="confirm-copy">“{pendingDelete.title}” akan dihapus permanen dari history.</p><div className="permission-actions"><button className="deny-button" onClick={() => setPendingDelete(null)}>Batal</button><button className="delete-confirm-button" onClick={confirmDeleteHistory}>Hapus</button></div></div></div>}
  </main>
}

export default App
