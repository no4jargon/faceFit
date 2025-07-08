import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { FaceMesh, FACEMESH_TESSELATION } from '@mediapipe/face_mesh'
import { drawConnectors } from '@mediapipe/drawing_utils'
import './index.css'

const API_URL = 'https://facefit-nntu.onrender.com/api/analyze-face'

function App() {
  const [image, setImage] = useState(null)
  const [method, setMethod] = useState('mediapipe')
  const [apiKey, setApiKey] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const [mode, setMode] = useState('upload') // upload or selfie
  const [showCamera, setShowCamera] = useState(false)
  const [processing, setProcessing] = useState(false)

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const overlayRef = useRef(null)
  const faceMeshRef = useRef(null)

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

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (err) {
      console.error('Camera error', err)
    }
  }

  useEffect(() => {
    if (showCamera) {
      startCamera()
      const faceMesh = new FaceMesh({
        locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`,
      })
      faceMesh.setOptions({ maxNumFaces: 1 })
      faceMesh.onResults((res) => {
        if (!processing) return
        const canvas = overlayRef.current
        const ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        if (res.multiFaceLandmarks && res.multiFaceLandmarks[0]) {
          drawConnectors(ctx, res.multiFaceLandmarks[0], FACEMESH_TESSELATION, { color: '#0f0', lineWidth: 1 })
        }
      })
      faceMeshRef.current = faceMesh
    }
  }, [showCamera, processing])

  const animateProcessing = () => {
    const start = Date.now()
    const loop = async () => {
      const video = videoRef.current
      const canvas = overlayRef.current
      if (!video || !canvas) return
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      const frame = ctx.getImageData(0, 0, canvas.width, canvas.height)
      const edgeData = sobel(frame)
      ctx.putImageData(edgeData, 0, 0)
      if (faceMeshRef.current) {
        await faceMeshRef.current.send({ image: video })
      }
      if (Date.now() - start < 5000 && processing) {
        requestAnimationFrame(loop)
      } else {
        setProcessing(false)
      }
    }
    requestAnimationFrame(loop)
  }

  const captureSelfie = async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const base64 = canvas.toDataURL('image/jpeg').split(',')[1]
    setProcessing(true)
    animateProcessing()
    try {
      const payload = { image: base64, method: 'openai' }
      const res = await axios.post(API_URL, payload)
      setResult(res.data)
      setError(null)
    } catch (err) {
      console.error('API error:', err)
      const msg = err.response?.data?.detail || err.message || 'Unable to analyze image'
      setError(msg)
    }
  }

  const sobel = (imageData) => {
    const { width, height, data } = imageData
    const gray = new Float32Array(width * height)
    for (let i = 0; i < gray.length; i++) {
      const j = i * 4
      gray[i] = 0.299 * data[j] + 0.587 * data[j + 1] + 0.114 * data[j + 2]
    }
    const out = new Uint8ClampedArray(width * height * 4)
    const get = (x, y) => gray[y * width + x]
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        let gx =
          -get(x - 1, y - 1) - 2 * get(x - 1, y) - get(x - 1, y + 1) +
          get(x + 1, y - 1) + 2 * get(x + 1, y) + get(x + 1, y + 1)
        let gy =
          -get(x - 1, y - 1) - 2 * get(x, y - 1) - get(x + 1, y - 1) +
          get(x - 1, y + 1) + 2 * get(x, y + 1) + get(x + 1, y + 1)
        const mag = Math.sqrt(gx * gx + gy * gy)
        const idx = (y * width + x) * 4
        out[idx] = out[idx + 1] = out[idx + 2] = mag > 128 ? 255 : 0
        out[idx + 3] = 255
      }
    }
    return new ImageData(out, width, height)
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 gap-4 max-w-md mx-auto">
      <h1 className="text-2xl font-bold">FaceFit</h1>
      <div className="flex gap-2">
        <button
          className={mode === 'upload' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'border px-3 py-1'}
          onClick={() => {
            setMode('upload')
            setShowCamera(false)
          }}
        >
          Upload Image
        </button>
        <button
          className={mode === 'selfie' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'border px-3 py-1'}
          onClick={() => {
            setMode('selfie')
            setShowCamera(true)
          }}
        >
          Take Selfie
        </button>
      </div>
      {mode === 'upload' && (
        <>
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
        </>
      )}
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
      {showCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex flex-col items-center justify-center z-50">
          <div className="relative">
            <video ref={videoRef} className="w-80 h-auto" autoPlay playsInline />
            <canvas ref={overlayRef} className="absolute top-0 left-0" />
          </div>
          <button onClick={captureSelfie} className="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
            Selfie
          </button>
          <button onClick={() => setShowCamera(false)} className="mt-2 text-white underline">
            Close
          </button>
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}
    </div>
  )
}

export default App
