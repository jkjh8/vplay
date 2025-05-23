import path from 'path'

import express from 'express'

import multer from 'multer'
import logger from '../../../../logger'
import { mediaPath } from '../../../../api/files/folder'

const router = express.Router()

const upload = multer({
  storage: multer.diskStorage({
    destination: (req, res, cb) => {
      const { uploadPath } = req.headers
      const currentPath = uploadPath
        ? path.join(mediaPath, uploadPath)
        : mediaPath
      logger.info('Upload path:', currentPath)
      cb(null, currentPath)
    },
    filename: (req, file, cb) => {
      cb(null, decodeURIComponent(file.fieldname))
    }
  })
})

router.post('/upload', upload.any(), (req, res) => {
  try {
    console.log(req.files)
    res.status(200).json({
      message: 'File uploaded successfully',
      files: req.files
    })
  } catch (error) {
    logger.error('File upload error:', error)
    res.status(500).json({
      message: 'File upload failed',
      error: error.message
    })
  }
})

export default router
