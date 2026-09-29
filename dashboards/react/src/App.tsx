import { NavLink, Route, Routes } from 'react-router-dom'
import './App.css'
import { Overview } from './pages/Overview'
import { PipelineHealth } from './pages/PipelineHealth'
import { Progression } from './pages/Progression'
import { TeamCompare } from './pages/TeamCompare'

const links = [
  { to: '/', label: 'Overview', end: true },
  { to: '/progression', label: 'Progression' },
  { to: '/compare', label: 'Team Compare' },
  { to: '/pipeline', label: 'Pipeline Health' },
]

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="dot" />
          Football Analytics
        </div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/progression" element={<Progression />} />
          <Route path="/compare" element={<TeamCompare />} />
          <Route path="/pipeline" element={<PipelineHealth />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
