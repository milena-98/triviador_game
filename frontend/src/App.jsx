import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000/api/auth'
const AVATARS = ['knight-1', 'knight-2', 'knight-3', 'knight-4']

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

function formatErrors(errors) {
  if (!errors) return 'Request failed.'

  const flattened = Object.values(errors).flat().join(' ')
  return flattened || 'Request failed.'
}

async function apiRequest(path, options = {}) {
  const method = options.method || 'GET'
  const isUnsafe = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method.toUpperCase())

  const headers = {
    ...(options.headers || {}),
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (isUnsafe) {
    const token = getCookie('csrftoken')
    if (token) {
      headers['X-CSRFToken'] = token
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : null

  if (!response.ok) {
    const message = payload && payload.errors ? formatErrors(payload.errors) : 'Request failed.'
    throw new Error(message)
  }

  return payload
}

async function fetchCsrf() {
  await fetch(`${API_BASE}/csrf/`, { credentials: 'include', method: 'GET' })
}

function App() {
  const [mode, setMode] = useState('login')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [errors, setErrors] = useState({})
  const [form, setForm] = useState({
    username: '',
    email: '',
    nickname: '',
    password: '',
    password_confirm: '',
  })

  const profileForm = useMemo(
    () => ({
      nickname: user?.profile?.nickname || '',
      avatar_key: user?.profile?.avatar_key || 'knight-1',
    }),
    [user],
  )

  const loadCurrentUser = async () => {
    try {
      await fetchCsrf()
      const data = await apiRequest('/me/')
      setUser(data)
      setErrors({})
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCurrentUser()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleProfileChange = (event) => {
    const { name, value } = event.target
    setUser((current) => ({
      ...current,
      profile: {
        ...current.profile,
        [name]: value,
      },
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setErrors({})

    try {
      await fetchCsrf()
      const payload = mode === 'register'
        ? {
            username: form.username,
            email: form.email,
            nickname: form.nickname,
            password: form.password,
            password_confirm: form.password_confirm,
          }
        : {
            username: form.username,
            password: form.password,
          }

      const endpoint = mode === 'register' ? '/register/' : '/login/'
      const data = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      setUser(data)
      setForm({ username: '', email: '', nickname: '', password: '', password_confirm: '' })
      setMessage(mode === 'register' ? 'Registration successful.' : 'Login successful.')
    } catch (error) {
      const messageText = error.message || 'Something went wrong.'
      setMessage(messageText)
      setErrors({ general: messageText })
    }
  }

  const handleProfileSave = async (event) => {
    event.preventDefault()
    setMessage('')

    try {
      await fetchCsrf()
      const updated = await apiRequest('/me/', {
        method: 'PATCH',
        body: JSON.stringify({
          nickname: user.profile.nickname,
          avatar_key: user.profile.avatar_key,
        }),
      })
      setUser(updated)
      setMessage('Profile updated successfully.')
    } catch (error) {
      setMessage(error.message)
    }
  }

  const handleLogout = async () => {
    try {
      await fetchCsrf()
      await apiRequest('/logout/', { method: 'POST' })
      setUser(null)
      setMessage('You have been logged out.')
    } catch (error) {
      setMessage(error.message)
    }
  }

  if (loading) {
    return <div className="app-shell"><div className="auth-card"><h2>Loading...</h2></div></div>
  }

  return (
    <div className="app-shell">
      <div className="auth-card">
        {!user ? (
          <>
            <div className="toggle-row">
              <button
                type="button"
                className={mode === 'login' ? 'toggle active' : 'toggle'}
                onClick={() => setMode('login')}
              >
                Login
              </button>
              <button
                type="button"
                className={mode === 'register' ? 'toggle active' : 'toggle'}
                onClick={() => setMode('register')}
              >
                Register
              </button>
            </div>

            <h1>{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>

            <form onSubmit={handleSubmit} className="auth-form">
              <label>
                Username
                <input name="username" value={form.username} onChange={handleChange} required />
              </label>

              {mode === 'register' && (
                <>
                  <label>
                    Email
                    <input name="email" type="email" value={form.email} onChange={handleChange} required />
                  </label>

                  <label>
                    Nickname
                    <input name="nickname" value={form.nickname} onChange={handleChange} required />
                  </label>
                </>
              )}

              <label>
                Password
                <input name="password" type="password" value={form.password} onChange={handleChange} required />
              </label>

              {mode === 'register' && (
                <label>
                  Confirm password
                  <input
                    name="password_confirm"
                    type="password"
                    value={form.password_confirm}
                    onChange={handleChange}
                    required
                  />
                </label>
              )}

              {message && <p className="message">{message}</p>}
              {errors.general && <p className="error">{errors.general}</p>}

              <button className="primary" type="submit">
                {mode === 'login' ? 'Login' : 'Register'}
              </button>
            </form>
          </>
        ) : (
          <>
            <div className="profile-header">
              <div>
                <p className="eyebrow">Current player</p>
                <h1>{user.profile.nickname}</h1>
              </div>
              <button type="button" className="ghost" onClick={handleLogout}>Logout</button>
            </div>

            <div className="profile-card">
              <p><strong>Username:</strong> {user.username}</p>
              <p><strong>Email:</strong> {user.email}</p>
            </div>

            <form onSubmit={handleProfileSave} className="auth-form">
              <label>
                Nickname
                <input
                  name="nickname"
                  value={user.profile.nickname}
                  onChange={handleProfileChange}
                  required
                />
              </label>

              <label>
                Avatar
                <select
                  name="avatar_key"
                  value={user.profile.avatar_key}
                  onChange={handleProfileChange}
                >
                  {AVATARS.map((avatar) => (
                    <option key={avatar} value={avatar}>{avatar}</option>
                  ))}
                </select>
              </label>

              {message && <p className="message">{message}</p>}

              <button type="submit" className="primary">Save profile</button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

export default App
