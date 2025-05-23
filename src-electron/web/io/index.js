import appServer from '../index.js'
import http from 'http'
import { Server } from 'socket.io'
import logger from '../../logger/index.js'

const httpServer = http.createServer(appServer)
const io = new Server(httpServer)

const initIoServer = (httpPort) => {
  try {
    let PORT = null
    if (httpPort === undefined || httpPort === null) {
      PORT = process.env.PORT || 3000
    } else {
      PORT = httpPort
    }
    httpServer.listen(PORT, () => {
      logger.info(`IO server listening on port ${PORT}`)
    })
  } catch (error) {
    logger.error('Error initializing IO server:', error)
  }
}

export { io, initIoServer }
