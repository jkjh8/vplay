import path from 'path'
import express from 'express'
// import { app } from 'electron'
// import logger from '../logger'

import cors from 'cors'
import cookieParser from 'cookie-parser'
import httpLogger from 'morgan'
// import session from 'express-session'
import routes from './routes'

console.log(process.env.QUASAR_PUBLIC_FOLDER)
const publicFolder = path.resolve(process.env.QUASAR_PUBLIC_FOLDER)

const appServer = express()

appServer.use(express.json())
appServer.use(express.urlencoded({ extended: true }))
appServer.use(cookieParser())

if (process.env.NODE_ENV === 'development') {
  appServer.use(httpLogger('dev'))
  appServer.use(
    cors({
      origin: (origin, callback) => {
        callback(null, origin)
      }
    })
  )
}

appServer.use(express.static(path.join(publicFolder, 'spa')))
appServer.use('/', routes)

export default appServer
