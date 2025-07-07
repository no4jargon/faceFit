import { useState } from 'react'
import axios from 'axios'
import './index.css'

const API_URL = 'https://facefit-nntu.onrender.com/api/analyze-face'

function App() {
  const [image, setImage] = useState(null)
  const [method, setMethod] = useState('mediapipe')
  const [apiKey, setApiKey] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFile = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1]
      setImage(base64)
    }
    reader.readAsDataURL(file)
  }

  const processImage = async () => {
    if (!image) return
    try {
      const payload = { image, method, api_key: apiKey }
      const res = await axios.post(API_URL, payload)
      setResult(res.data)
      setError(null)
    } catch (err) {
      console.error('API error:', err)
      const msg = err.response?.data?.detail || err.message || 'Unable to analyze image'
      setError(msg)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 gap-4">
      <h1 className="text-2xl font-bold">FaceFit</h1>
      <input type="file" accept="image/*" onChange={handleFile} className="border p-2" />
      <select value={method} onChange={(e) => setMethod(e.target.value)} className="border p-2">
        <option value="mediapipe">Mediapipe Ratios</option>
        <option value="openai">OpenAI</option>
        <option value="gemini">Gemini</option>
        <option value="open_source">Open Source VLM</option>
      </select>
      {(method === 'openai' || method === 'gemini') && (
        <input
          type="text"
          placeholder="API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="border p-2 w-72"
        />
      )}
      <button onClick={processImage} className="bg-blue-500 text-white px-4 py-2 rounded">
        Process
      </button>
      {error && <p className="text-red-500">{error}</p>}
      {result && (
        <div className="mt-4 text-center">
          <h2 className="text-xl font-semibold">Face Shape: {result.face_shape}</h2>
          <div className="mt-2">
            <p className="font-semibold">Recommended:</p>
            <ul>
              {result.recommendations.recommended.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="mt-2">
            <p className="font-semibold">Avoid:</p>
            <ul>
              {result.recommendations.avoid.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          {result.ratios && (
            <div className="mt-4">
              <p className="font-semibold">Face Ratios:</p>
              <ul className="list-disc list-inside text-left inline-block">
                <li>
                  <span className="font-medium">Face Length / Cheekbone Width:</span>{' '}
                  {result.ratios.face_length_width_ratio.toFixed(2)}
                </li>
                <li>
                  <span className="font-medium">Forehead / Jaw Width:</span>{' '}
                  {result.ratios.forehead_jaw_ratio.toFixed(2)}
                </li>
                <li>
                  <span className="font-medium">Jaw / Cheekbone Width:</span>{' '}
                  {result.ratios.jaw_cheekbone_ratio.toFixed(2)}
                </li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
