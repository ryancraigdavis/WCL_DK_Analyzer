import React, { useState } from 'react'
import './tabs.css'

export const Tabs = ({ children, defaultTab = 0 }) => {
  const [activeTab, setActiveTab] = useState(defaultTab)

  return (
    <div className="tabs-container">
      <div className="tab-headers">
        {children.map((child, index) => (
          <button
            key={index}
            className={`tab-header ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {child.props.icon && (
              <span className="tab-icon">{child.props.icon}</span>
            )}
            {child.props.label}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {children[activeTab]}
      </div>
    </div>
  )
}

export const Tab = ({ children, label, icon }) => {
  return <div className="tab-panel">{children}</div>
}