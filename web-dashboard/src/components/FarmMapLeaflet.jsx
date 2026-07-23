import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix default marker icons with Vite
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

const greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

const redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

export default function FarmMapLeaflet({ farms, riskIds, center }) {
  return (
    <MapContainer center={[center.lat, center.lng]} zoom={12} style={{ height: '580px', width: '100%' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {farms.map((farm) => (
        <Marker
          key={farm.id}
          position={[farm.lat, farm.lon]}
          icon={farm.healthy ? greenIcon : redIcon}
        >
          <Popup>
            <strong>{farm.name}</strong>
            <br />
            Crop: {farm.crop}
            {!farm.healthy && (
              <>
                <br />
                <span style={{ color: '#dc2626' }}>⚠ {farm.disease}</span>
              </>
            )}
          </Popup>
        </Marker>
      ))}
      {farms.filter((f) => !f.healthy).map((farm) => (
        <Circle
          key={`risk-${farm.id}`}
          center={[farm.lat, farm.lon]}
          radius={riskIds.has(farm.id) ? 800 : 500}
          pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.12 }}
        />
      ))}
    </MapContainer>
  )
}
