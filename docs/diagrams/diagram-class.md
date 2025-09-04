```mermaid
classDiagram
    class Agent {
        +parseInstruction(naturalText): DSL
        +generateDSL()
    }

    class Runner {
        +executePlan(DSL)
        +handleStep(step)
    }

    class Authenticator {
        +verifyTOTP(secret)
        +issueJWT(user)
    }

    class Downloader {
        +waitForDownload(pattern)
        +verifyFile(hash)
    }

    class Logger {
        +writeLog(step, result)
        +auditTrail()
    }

    class StorageClient {
        +saveFile(path, bucket)
        +loadFile(path)
    }

    class PolicyEngine {
        +checkPermission(user, action)
    }

    Agent --> Runner
    Runner --> Downloader
    Runner --> Logger
    Runner --> Authenticator
    Downloader --> StorageClient
    Logger --> StorageClient
    Runner --> PolicyEngine
