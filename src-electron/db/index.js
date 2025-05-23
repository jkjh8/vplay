import { app } from 'electron'
import path from 'path'
import Datastore from 'nedb-promises'
import logger from '../logger'

let dbStatus = null
let dbFiles = null
let dbPlaylists = null

const dbDir = path.join(app.getPath('appData'), 'db')
const dbFilesPath = path.join(dbDir, 'files.db')
const dbPlaylistsPath = path.join(dbDir, 'playlists.db')
const dbStatusPath = path.join(dbDir, 'status.db')

const dbInit = async () => {
  try {
    dbFiles = Datastore.create({
      filename: dbFilesPath,
      autoload: true
    })
    dbPlaylists = Datastore.create({
      filename: dbPlaylistsPath,
      autoload: true
    })
    dbStatus = Datastore.create({
      filename: dbStatusPath,
      autoload: true
    })
  } catch (error) {
    logger.error('Error initializing database:', error)
  }
}

export { dbInit, dbFiles, dbPlaylists, dbStatus }
