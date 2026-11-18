import { useEffect, useRef } from 'react'
import { WS_BASE, withToken } from './backend'
import type { StudioEvent } from './types'

/** Subscribe to live backend events; reconnects automatically. */
export function useEvents(onEvent: (event: StudioEvent) => void): void {
  const handler = useRef(onEvent)
  handler.current = onEvent

  useEffect(() => {
    let socket: WebSocket | null = null
    let retry: ReturnType<typeof setTimeout> | null = null
    let closed = false

    const connect = (): void => {
      socket = new WebSocket(withToken(`${WS_BASE}/ws`))
      socket.onmessage = (msg) => {
        try {
          handler.current(JSON.parse(msg.data as string) as StudioEvent)
        } catch {
          /* malformed event: ignore */
        }
      }
      socket.onclose = () => {
        if (!closed) retry = setTimeout(connect, 2000)
      }
    }
    connect()

    return () => {
      closed = true
      if (retry) clearTimeout(retry)
      socket?.close()
    }
  }, [])
}
