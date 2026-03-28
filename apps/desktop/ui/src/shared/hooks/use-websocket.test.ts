import { describe, it, expect, beforeEach } from 'vitest'
import { useWSStore } from './use-websocket'

describe('useWSStore', () => {
  beforeEach(() => {
    useWSStore.setState({ connected: false, lastEvent: null, listeners: new Map() })
  })

  it('starts disconnected', () => {
    expect(useWSStore.getState().connected).toBe(false)
  })

  it('tracks connection state', () => {
    useWSStore.getState().setConnected(true)
    expect(useWSStore.getState().connected).toBe(true)
  })

  it('stores last event', () => {
    const event = { event_type: 'test', data: { foo: 'bar' } }
    useWSStore.getState().setLastEvent(event)
    expect(useWSStore.getState().lastEvent).toEqual(event)
  })

  it('notifies subscribers on event', () => {
    let received: unknown = null
    useWSStore.getState().subscribe('test_event', (e) => {
      received = e
    })
    const event = { event_type: 'test_event', data: { value: 1 } }
    useWSStore.getState().setLastEvent(event)
    expect(received).toEqual(event)
  })

  it('notifies wildcard subscribers', () => {
    let received: unknown = null
    useWSStore.getState().subscribe('*', (e) => {
      received = e
    })
    const event = { event_type: 'anything', data: {} }
    useWSStore.getState().setLastEvent(event)
    expect(received).toEqual(event)
  })

  it('unsubscribe removes listener', () => {
    let count = 0
    const unsub = useWSStore.getState().subscribe('counter', () => {
      count++
    })
    useWSStore.getState().setLastEvent({ event_type: 'counter' })
    expect(count).toBe(1)

    unsub()
    useWSStore.getState().setLastEvent({ event_type: 'counter' })
    expect(count).toBe(1) // Not incremented after unsub
  })
})
