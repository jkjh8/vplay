import { app } from 'electron'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import logger from './logger'
import { dbInit } from './db'
import { initIoServer } from './web/io'
import { existsMediaPath, existsTmpPath } from './api/files/folder'
import { runPythonScript, killPythonProcess } from './run_python'

// needed in case process is undefined under Linux
// const platform = process.platform || os.platform()

const currentDir = fileURLToPath(new URL('.', import.meta.url))

let mainWindow

async function initServer() {
  existsTmpPath()
  logger.info('Check Tmp Path')
  existsMediaPath()
  logger.info('Check Media Path')
  await dbInit()
  logger.info('Database initialized')
  initIoServer(3000)
}

// async function createWindow() {
//   /**
//    * Initial window options
//    */
//   mainWindow = new BrowserWindow({
//     icon: path.resolve(currentDir, 'icons/icon.png'), // tray icon
//     width: 1000,
//     height: 600,
//     useContentSize: true,
//     webPreferences: {
//       contextIsolation: true,
//       // More info: https://v2.quasar.dev/quasar-cli-vite/developing-electron-apps/electron-preload-script
//       preload: path.resolve(
//         currentDir,
//         path.join(
//           process.env.QUASAR_ELECTRON_PRELOAD_FOLDER,
//           'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION
//         )
//       )
//     }
//   })

//   if (process.env.DEV) {
//     await mainWindow.loadURL(process.env.APP_URL)
//   } else {
//     await mainWindow.loadFile('index.html')
//   }

//   if (process.env.DEBUGGING) {
//     // if on DEV or Production with debug enabled
//     mainWindow.webContents.openDevTools()
//   } else {
//     // we're on production; no access to devtools pls
//     mainWindow.webContents.on('devtools-opened', () => {
//       mainWindow.webContents.closeDevTools()
//     })
//   }

//   mainWindow.on('closed', () => {
//     mainWindow = null
//   })
// }

app.whenReady().then(async () => {
  await initServer()
  // createWindow()
  // Run Python script
  runPythonScript('player.py', [])
  logger.info('Python script started')
})

app.on('window-all-closed', () => {
  killPythonProcess()
  app.quit()
})

app.on('activate', () => {
  if (mainWindow === null) {
    // createWindow()
  }
})
