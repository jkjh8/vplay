// 파이썬 실행 코드
import { spawn } from 'child_process'
import path from 'path'

let pythonProcess = null

// 파이썬 실행 함수
function runPythonScript(scriptPath, args = []) {
  if (pythonProcess && !pythonProcess.killed) {
    console.log('Python process is already running.')
    return
  }

  const projectRoot = process.cwd()
  // venv 경로설정
  const pythonPath = path.join(
    projectRoot,
    'src-electron',
    'run_python',
    'player',
    '.venv',
    'Scripts',
    'python.exe'
  )
  // 스크립트 경로 설정
  const script = path.join(
    projectRoot,
    'src-electron',
    'run_python',
    'player',
    scriptPath
  )
  console.log(`Python script path: ${script}`)
  console.log(`Python path: ${pythonPath}`)

  // 스크립트 실행 - Windows 경로 공백 문제 해결
  pythonProcess = spawn(pythonPath, [script, ...args], {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: false // shell을 false로 변경하여 경로 문제 해결
  })

  if (!pythonProcess || typeof pythonProcess.on !== 'function') {
    console.error('Failed to spawn Python process.')
    return
  }

  // 에러 처리
  pythonProcess.stdout.on('data', (data) =>
    console.log(`Python stdout: ${data}`)
  )
  pythonProcess.stderr.on('data', (data) =>
    console.error(`Python stderr: ${data}`)
  )
  pythonProcess.on('error', (error) => console.error(`Error: ${error}`))
  // 종료 처리
  pythonProcess.on('exit', (code) => {
    pythonProcess = null
    if (code !== 0) {
      console.error(`Python script exited with code ${code}`)
    } else {
      console.log('Python script executed successfully')
    }
  })
}

// 프로세스 종료 함수
function killPythonProcess() {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
    pythonProcess = null
  }
}

// 모듈 내보내기
export { runPythonScript, killPythonProcess }
