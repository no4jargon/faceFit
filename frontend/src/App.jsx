import { useState } from 'react'
import axios from 'axios'
import './index.css'

function App() {
  const [image, setImage] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = async () => {
      const base64 = reader.result.split(',')[1]
      try {
        const res = await axios.post('/api/analyze-face', { image: base64 })
        setResult(res.data)
        setError(null)
      } catch (err) {
        setError('Unable to analyze image')
      }
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 gap-4">
      <h1 className="text-2xl font-bold">FaceFit</h1>
      <input type="file" accept="image/*" onChange={handleFile} className="border p-2" />
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
