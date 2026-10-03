# Compliance matrix

| Requirement | File | Artifact | Status |
|---|---|---|---|
| Shared output contract across photo/video/LiDAR | [src/property_scan/common/output_contract.py](../src/property_scan/common/output_contract.py) | JSON schema and dataclasses | Implemented |
| Photo pipeline skeleton | [src/property_scan/pipeline/photo.py](../src/property_scan/pipeline/photo.py) | Multi-room room-folder processor | Implemented |
| Video pipeline skeleton | [src/property_scan/pipeline/video.py](../src/property_scan/pipeline/video.py) | Walkthrough reconstruction template | Implemented |
| LiDAR pipeline skeleton | [src/property_scan/pipeline/lidar.py](../src/property_scan/pipeline/lidar.py) | Pro-device geometric processing template | Implemented |
| CLI entry point | [src/property_scan/cli.py](../src/property_scan/cli.py) | One-command JSON generation | Implemented |
| Capture protocol | [docs/capture_protocol.md](capture_protocol.md) | Field procedure for users | Implemented |
| Device matrix | [docs/device_matrix.md](device_matrix.md) | Hardware and confidence mapping | Implemented |
| Benchmark model | [benchmark/benchmark_summary.md](../benchmark/benchmark_summary.md) | Benchmarks, gates, and repeatability plan | Implemented |
| Technical narrative | [docs/technical_report.md](technical_report.md) | Six-page architecture summary | Implemented |

## Notes

The repository is intentionally structured as a production-ready starter. It contains the core architectural pieces necessary to satisfy the assignment while staying honest about the fact that real benchmark captures are not available in the local workspace.
