const buttonId = "dk-analyze-btn"
const iframeId = "dk-analyze-iframe"
let currentParams = null
const localIDs = [
  "aeieohnbigjehliffdcpnaegkiekbdlb",
  "dpdollnoobppbpcnfneijbmlkddpfaeg",
  "pjomadfjjobkggnpjjhnfhccjkgmplpj",
]

function isEqual(obj1, obj2) {
    var props1 = Object.getOwnPropertyNames(obj1);
    var props2 = Object.getOwnPropertyNames(obj2);

    if (props1.length !== props2.length) {
        return false;
    }
    for (let i = 0; i < props1.length; i++) {
        let val1 = obj1[props1[i]];
        let val2 = obj2[props1[i]];
        let isObjects = isObject(val1) && isObject(val2);
        if (isObjects && !isEqual(val1, val2) || !isObjects && val1 !== val2) {
            return false;
        }
    }
    return true;
}

function isObject(object) {
  return object != null && typeof object === 'object';
}

function init() {
  const url = window.location.href
  console.log('Init called with URL:', url)

  if (!url.includes('fight=')) {
    console.log('Hiding button: No fight parameter')
    hideButton()
    removeIframe()
    return
  }

  if (!url.includes('source=')) {
    console.log('Hiding button: No source parameter')
    hideButton()
    removeIframe()
    return
  }

  if (!url.includes('/reports/')) {
    console.log('Hiding button: Not a report page')
    hideButton()
    removeIframe()
    return
  }

  addAnalyzeButton()

  const params = parseParams()
  if (currentParams && !isEqual(currentParams, params)) {
    console.log('Parameters changed, updating iframe')
    document.getElementById(iframeId).src = getFrameURL(params)
    currentParams = params
  }
}

function hideButton() {
  const button = document.getElementById(buttonId)

  if (button) {
    button.style.setProperty("display", "none", "important")
  }
}

function removeIframe() {
  const iframe = document.getElementById(iframeId)

  if (iframe) {
    iframe.remove()
  }

  currentParams = null
}

function parseParams() {
  const url = window.location.href
  console.log('Parsing URL:', url)
  
  try {
    // Get the report ID from the path - more flexible matching
    const reportMatch = url.match(/reports\/([^/?#]+)/)
    if (!reportMatch) throw new Error('Could not find report ID in URL')
    const report = reportMatch[1]
    
    // Get parameters from URL search params - more reliable than regex
    const urlParams = new URLSearchParams(window.location.search)
    const fightParam = urlParams.get('fight')
    const sourceParam = urlParams.get('source')
    
    if (!fightParam) throw new Error('No fight parameter found')
    if (!sourceParam) throw new Error('No source parameter found')
    
    // Convert fight parameter
    const fight = fightParam === "last" ? -1 : fightParam
    
    console.log('Successfully parsed params:', { fight, source: sourceParam, report })
    
    return {
      fight,
      source: sourceParam,
      report
    }
  } catch (error) {
    console.error('Error parsing URL parameters:', error)
    console.log('URL parts:', {
      pathname: window.location.pathname,
      search: window.location.search,
      hash: window.location.hash
    })
    return null
  }
}


function hideReport() {
  document.getElementById("report-view-contents").style.display = "none"
}

function showReport() {
  document.getElementById("report-view-contents").style.display = "block"
}

function addLocationObserver(callback) {
  const config = { attributes: false, childList: true, subtree: true }
  const observer = new MutationObserver(callback)
  observer.observe(document.body, config)
}

function debounce(func, timeout = 300){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(this, args); }, timeout);
  };
}

function handler() {
  if (document.getElementById(iframeId)) {
    return
  }

  document.body.classList.remove("compare")
  hideReport()

  const iframe = document.createElement("iframe")
  const params = parseParams()
  iframe.src = getFrameURL(params)
  iframe.setAttribute("id", iframeId)
  iframe.style = "min-width:100%;border:none;overflow:hidden;"
  iframe.scrolling = "no"
  const report_node = document.getElementById("report-view-contents")
  report_node.parentNode.insertBefore(iframe, report_node)
  currentParams = params

  // debounce to prevent flickering
  window.addEventListener("message", debounce(e => {
    if (e.data > 0) {
      document.getElementById(iframeId).height = e.data + 'px';
    }
  }, 10))
}

function getFrameURL(params) {
  if (window.chrome && localIDs.includes(window.chrome.runtime.id)) {
    return `http://localhost:5173?${new URLSearchParams(params)}`
  }
  return `https://d4a6eolggrfst.cloudfront.net/?${new URLSearchParams(params)}`
}

function addAnalyzeButton() {
  let button = document.getElementById(buttonId)

  if (button) {
    button.style.display = "block"
    return
  }

  button = document.createElement("a")
  button.setAttribute("id", buttonId)
  button.className = "big-tab view-type-tab"

  const icon = document.createElement("span")
  icon.className = "zmdi zmdi-eye"
  icon.style.color = "darkred"

  const text = document.createElement("span")
  text.innerHTML = "<br> DK Analyze"
  text.className = "big-tab-text"
  text.style.color = "darkred"

  const tabs = document.getElementById("top-level-view-tabs")
  button.appendChild(icon)
  button.appendChild(text)
  button.onclick = handler
  tabs.onclick = (e) => {
    const btn = document.getElementById(buttonId)
    const target = e.target

    if (!target.isEqualNode(btn) && !target.parentNode.isEqualNode(btn)) {
      btn.classList.remove("selected")
      removeIframe()
      showReport()
    }
  }
  tabs.insertBefore(button, tabs.firstChild)
}

addLocationObserver(init)
init()
