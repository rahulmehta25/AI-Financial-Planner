import React, { createContext, useContext, useState, useEffect } from 'react'

interface DemoContextType {
  isDemoMode: boolean
  enableDemoMode: () => void
  disableDemoMode: () => void
}

const DemoContext = createContext<DemoContextType>({
  isDemoMode: false,
  enableDemoMode: () => {},
  disableDemoMode: () => {},
})

export const useDemo = () => {
  const context = useContext(DemoContext)
  if (!context) {
    throw new Error('useDemo must be used within a DemoProvider')
  }
  return context
}

export const DemoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(true)

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const demoParam = urlParams.get('demo')
    if (demoParam === 'false') {
      setIsDemoMode(false)
    }
  }, [])

  const enableDemoMode = () => {
    setIsDemoMode(true)
    localStorage.setItem('demoMode', 'true')
  }

  const disableDemoMode = () => {
    setIsDemoMode(false)
    localStorage.removeItem('demoMode')
  }

  return (
    <DemoContext.Provider value={{ isDemoMode, enableDemoMode, disableDemoMode }}>
      {children}
    </DemoContext.Provider>
  )
}