import * as winston from 'winston'
import DailyRotateFile from 'winston-daily-rotate-file'
import path from 'path'
import { app } from 'electron'

const { combine, timestamp, printf, colorize } = winston.format

const logDir = path.join(app.getPath('appData'), 'logs')

const levels = {
  error: 0,
  warn: 1,
  info: 2,
  verbose: 3,
  debug: 4
}

const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  verbose: 'cyan',
  debug: 'blue'
}
winston.addColors(colors)

const logFormat = combine(
  timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  printf((info) => {
    if (info.stack) {
      return `${info.timestamp} ${info.level}: ${info.message} \n ${info.stack}`
    }
    return `${info.timestamp} ${info.level}: ${info.message}`
  })
)

const consoleOpts = {
  handleExceptions: true,
  level: 'debug',
  format: combine(
    colorize({ all: true }),
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' })
  )
}

const transports = [
  new winston.transports.Console(consoleOpts),
  new DailyRotateFile({
    level: 'debug',
    datePattern: 'YYYY-MM-DD',
    filename: '%DATE%.log',
    dirname: logDir,
    maxFiles: 30,
    zippedArchive: true
  }),
  new DailyRotateFile({
    level: 'error',
    datePattern: 'YYYY-MM-DD',
    filename: '%DATE%-error.log',
    dirname: path.join(logDir, 'error'),
    maxFiles: 30,
    zippedArchive: true
  })
]

const Logger = winston.createLogger({
  level: 'debug',
  levels,
  format: logFormat,
  transports
})

export default Logger
