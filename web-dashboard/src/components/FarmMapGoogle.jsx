import { useMemo, useState } from 'react'
import { GoogleMap, useJsApiLoader, Marker, Circle, InfoWindow } from '@react-google-maps/api'

const mapContainerStyle = { width: '100%', height: '580px' }

export default function FarmMapGoogle({ mapsKey, farms, riskData, center }) {
  const [selectedFarm, setSelectedFarm] = useState(null)
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: mapsKey,
    id: 'krishiiq-google-map',
  })

  const riskIds = useMemo(() => new Set(riskData.map((r) => r.farm_id)), [riskData])

  if (loadError) {
    return (
      <div className="p-6 text-red-600 text-sm">
        Google Maps error: {loadError.message}. Enable &quot;Maps JavaScript API&quot; for your key in Google Cloud Console.
      </div>
    )
  }

  if (!isLoaded) {
    return <div className="flex items-center justify-center h-[580px] text-gray-500">Loading Google Maps…</div>
  }

  return (
    <GoogleMap mapContainerStyle={mapContainerStyle} center={center} zoom={12} mapTypeId="hybrid">
      {farms.map((farm) => (
        <Marker
          key={farm.id}
          position={{ lat: farm.lat, lng: farm.lon }}
          onClick={() => setSelectedFarm(farm)}
          icon={{
            path: window.google?.maps?.SymbolPath?.CIRCLE,
            fillColor: farm.healthy ? '#16a34a' : '#dc2626',
            fillOpacity: 1,
            strokeColor: '#fff',
            strokeWeight: 2,
            scale: 10,
          }}
        />
      ))}
      {farms.filter((f) => !f.healthy).map((farm) => (
        <Circle
          key={`risk-${farm.id}`}
          center={{ lat: farm.lat, lng: farm.lon }}
          radius={riskIds.has(farm.id) ? 800 : 500}
          options={{
            fillColor: '#ef4444',
            fillOpacity: 0.12,
            strokeColor: '#ef4444',
            strokeOpacity: 0.4,
          }}
        />
      ))}
      {selectedFarm && (
        <InfoWindow
          position={{ lat: selectedFarm.lat, lng: selectedFarm.lon }}
          onCloseClick={() => setSelectedFarm(null)}
        >
          <div className="text-sm p-1">
            <div className="font-bold">{selectedFarm.name}</div>
            <div>Crop: {selectedFarm.crop}</div>
            {!selectedFarm.healthy && (
              <div className="text-red-600 font-medium">⚠ {selectedFarm.disease}</div>
            )}
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  )
}
