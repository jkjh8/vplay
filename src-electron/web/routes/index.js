// import path from 'path'
import express from 'express'
import api from './api/index.js'

const router = express.Router()

router.get('/', (req, res) => {
  res.send('Hello World!')
})

router.use('/api', api)

export default router
