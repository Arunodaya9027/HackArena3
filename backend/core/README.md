# GeoClear AI - Java Core API

Java Spring Boot application serving as the main API orchestrator for GeoClear AI.

## Responsibilities

1. **API Gateway**: RESTful endpoints for clients
2. **Data Ingestion**: Reading and parsing WKT files
3. **Orchestration**: Coordinating Python geometry engine calls
4. **Depth Metadata**: Managing Z-order and 3D visualization metadata
5. **Business Logic**: Priority management and validation

## Project Structure

```
src/main/java/com/geoclear/api/
├── controller/
│   └── GeoClearController.java        # REST API endpoints
├── service/
│   ├── GeoClearService.java           # Main orchestration service
│   ├── WktIngestionService.java       # WKT file parsing
│   └── DepthMetadataService.java      # 3D depth management
├── model/
│   ├── FeaturePriority.java           # Priority enum
│   ├── FeatureInput.java              # Input feature model
│   ├── GeometryRequest.java           # Request model
│   ├── GeometryResponse.java          # Response model
│   ├── DisplacementResult.java        # Result model
│   └── ConflictMetadata.java          # Conflict metadata
├── client/
│   └── PythonGeometryEngineClient.java # Python engine HTTP client
├── config/
│   └── AppConfig.java                 # Spring configuration
└── GeoClearApplication.java           # Main application class
```

## Building

```bash
mvn clean install
```

## Running

```bash
mvn spring-boot:run
```

Or run the JAR:
```bash
java -jar target/geoclear-java-api-1.0.0.jar
```

## Configuration

Edit `src/main/resources/application.properties`:

```properties
# Server
server.port=8080

# Python Engine
python.geometry.engine.url=http://localhost:8001
python.geometry.engine.process.endpoint=/api/geometry/process
python.geometry.engine.timeout=30000

# Logging
logging.level.com.geoclear.api=DEBUG
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Process Geometry
```
POST /api/geoclear/process
Content-Type: application/json

Body: GeometryRequest
```

### Process WKT File
```
POST /api/geoclear/process-file?filePath=<path>&defaultPriority=<P1_HIGHWAY|P2_ROAD>&minClearance=<number>
```

### Process WKT File (Auto-Priorities)
```
POST /api/geoclear/process-file-auto?filePath=<path>&minClearance=<number>
```

### API Info
```
GET /api/info
```

## Dependencies

- **Spring Boot 3.2.2**: Framework
- **Spring Web**: REST API
- **Spring Validation**: Input validation
- **Jackson**: JSON processing
- **Commons IO**: File operations
- **Lombok**: Boilerplate reduction

## Testing

```bash
mvn test
```

## Docker Support

Build Docker image:
```bash
docker build -t geoclear-java-api .
```

Run container:
```bash
docker run -p 8080:8080 -e PYTHON_ENGINE_URL=http://python-engine:8001 geoclear-java-api
```

## Development

### Adding New Features

1. Add model class in `model/` package
2. Add service logic in `service/` package
3. Add REST endpoint in `controller/` package
4. Update documentation

### Code Style

- Follow Java naming conventions
- Use Spring annotations appropriately
- Add JavaDoc for public methods
- Use SLF4J for logging

## Troubleshooting

**Python engine connection failed**:
- Verify Python engine is running on port 8001
- Check `python.geometry.engine.url` in properties
- Review firewall settings

**WKT file not found**:
- Use absolute paths or relative to execution directory
- Check file permissions

**Validation errors**:
- Ensure WKT format is correct: `LINESTRING(x1 y1, x2 y2, ...)`
- Check priority values: `P1_HIGHWAY` or `P2_ROAD`
- Verify minClearance is positive

## Production Deployment

1. Build with production profile: `mvn clean package -Pprod`
2. Configure external properties file
3. Set up monitoring (Actuator endpoints)
4. Configure SSL/TLS
5. Set up load balancer for multiple instances

---

**Java 17+ Required | Spring Boot 3.2.2**
