import express from 'express'
import path from 'path'

import files from './files'

const router = express.Router()

router.use('/files', files)

export default router
