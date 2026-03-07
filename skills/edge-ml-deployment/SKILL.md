---
name: edge-ml-deployment
description: Edge ML inference deployment with TensorRT, ONNX, quantization, Jetson optimization, RLDS, LeRobot, and data pipelines.
category: ai
tags: [edge-ml, tensorrt, onnx, quantization, jetson, deployment, inference, lerobot]
version: "1.0.0"
---

# Edge ML Deployment

Deploying ML models on edge devices for real-time robot control. This skill covers optimization, quantization, and deployment pipelines.

## When to Use

- Deploying perception models on embedded GPUs (Jetson, etc.)
- Optimizing models for real-time inference (< 10ms latency)
- Quantizing models to reduce memory and compute
- Converting PyTorch/TensorFlow to deployment formats (ONNX, TensorRT)
- Setting up data pipelines for robot learning
- Deploying VLA policies on edge devices

## Quick Start

```bash
# Install TensorRT
sudo apt install tensorrt

# Install ONNX
pip install onnx onnxruntime onnxruntime-gpu

# For Jetson
sudo apt install nvidia-jetpack

# For LeRobot
pip install lerobot
```

## Core Concepts

### 1. Model Optimization Pipeline

Convert and optimize models for edge deployment.

```python
import torch
import onnx
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

class ModelOptimizer:
    def __init__(self, model, input_shape):
        self.model = model
        self.input_shape = input_shape
    
    def export_onnx(self, output_path="model.onnx"):
        """Export PyTorch model to ONNX."""
        dummy_input = torch.randn(*self.input_shape)
        
        torch.onnx.export(
            self.model,
            dummy_input,
            output_path,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}},
            opset_version=13
        )
        
        # Verify
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        return output_path
    
    def build_tensorrt_engine(self, onnx_path, engine_path="model.trt", fp16=True):
        """Build TensorRT engine from ONNX."""
        logger = trt.Logger(trt.Logger.INFO)
        builder = trt.Builder(logger)
        network = builder.create_network(
            1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        )
        parser = trt.OnnxParser(network, logger)
        
        # Parse ONNX
        with open(onnx_path, "rb") as f:
            parser.parse(f.read())
        
        # Build config
        config = builder.create_builder_config()
        config.max_workspace_size = 1 << 30  # 1GB
        
        if fp16:
            config.set_flag(trt.BuilderFlag.FP16)
        
        # Build engine
        engine = builder.build_engine(network, config)
        
        # Save
        with open(engine_path, "wb") as f:
            f.write(engine.serialize())
        
        return engine
    
    def quantize_static(self, onnx_path, output_path="model_quant.onnx"):
        """Apply static quantization."""
        from onnxruntime.quantization import quantize_static, CalibrationDataReader
        
        class DataReader(CalibrationDataReader):
            def __init__(self):
                self.enum_data = []
                for _ in range(100):
                    self.enum_data.append(
                        np.random.randn(*self.input_shape).astype(np.float32)
                    )
                self.enum_data = iter(self.enum_data)
            
            def get_next(self):
                return next(self.enum_data, None)
        
        quantize_static(onnx_path, output_path, DataReader())
        return output_path
```

### 2. TensorRT Inference

High-performance inference on NVIDIA GPUs.

```python
import tensorrt as trt
import pycuda.driver as cuda
import numpy as np

class TensorRTInference:
    def __init__(self, engine_path):
        self.logger = trt.Logger(trt.Logger.WARNING)
        
        # Load engine
        with open(engine_path, "rb") as f:
            runtime = trt.Runtime(self.logger)
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
        self.context = self.engine.create_execution_context()
        
        # Allocate buffers
        self.allocate_buffers()
    
    def allocate_buffers(self):
        self.inputs = []
        self.outputs = []
        self.bindings = []
        
        for i in range(self.engine.num_bindings):
            shape = self.engine.get_binding_shape(i)
            size = trt.volume(shape)
            dtype = trt.nptype(self.engine.get_binding_dtype(i))
            
            # Allocate host and device memory
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            
            self.bindings.append(int(device_mem))
            
            if self.engine.binding_is_input(i):
                self.inputs.append({"host": host_mem, "device": device_mem})
            else:
                self.outputs.append({"host": host_mem, "device": device_mem})
    
    def infer(self, input_data):
        # Copy input to device
        np.copyto(self.inputs[0]["host"], input_data.ravel())
        cuda.memcpy_htod(self.inputs[0]["device"], self.inputs[0]["host"])
        
        # Execute
        self.context.execute_v2(bindings=self.bindings)
        
        # Copy output to host
        cuda.memcpy_dtoh(self.outputs[0]["host"], self.outputs[0]["device"])
        
        return self.outputs[0]["host"].copy()

# Usage
trt_infer = TensorRTInference("model.trt")
output = trt_infer infer(input_batch)
```

### 3. Jetson Deployment

Optimize for NVIDIA Jetson edge devices.

```bash
# On Jetson, use JetPack
sudo apt update
sudo apt install nvidia-jetpack

# MAXN mode for maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks

# Monitor
jtop  # Install with: sudo pip3 install jetson-stats
```

```python
# Jetson-specific optimizations
class JetsonOptimizer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def optimize_for_jetson(self, model):
        """Apply Jetson-specific optimizations."""
        # Convert to TorchScript
        model.eval()
        example_input = torch.randn(1, 3, 224, 224).to(self.device)
        
        # Trace
        traced_model = torch.jit.trace(model, example_input)
        
        # Optimize for inference
        optimized = torch.jit.optimize_for_inference(traced_model)
        
        return optimized
    
    def benchmark(self, model, input_shape, num_runs=100):
        """Benchmark inference latency."""
        import time
        
        dummy_input = torch.randn(*input_shape).to(self.device)
        
        # Warmup
        for _ in range(10):
            _ = model(dummy_input)
        
        # Benchmark
        torch.cuda.synchronize()
        start = time.time()
        
        for _ in range(num_runs):
            _ = model(dummy_input)
        
        torch.cuda.synchronize()
        elapsed = time.time() - start
        
        latency_ms = (elapsed / num_runs) * 1000
        fps = num_runs / elapsed
        
        print(f"Latency: {latency_ms:.2f} ms")
        print(f"FPS: {fps:.1f}")
        
        return latency_ms, fps
```

### 4. Robot Learning Data Pipeline

RLDS and LeRobot for robot learning datasets.

```python
# LeRobot dataset format
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset.create(
    repo_id="username/robot_task",
    robot_type="panda",
    fps=30,
    features={
        "observation.image": {"dtype": "image", "shape": (224, 224, 3), "names": ["height", "width", "channels"]},
        "observation.state": {"dtype": "float32", "shape": (7,), "names": ["joint_pos"]},
        "action": {"dtype": "float32", "shape": (7,), "names": ["joint_target"]},
    }
)

# Add episode
dataset.add_frame({"observation.image": image, "observation.state": state, "action": action})
dataset.save_episode()

# Load and train
from lerobot.common.policies.act.configuration_act import ACTConfig
from lerobot.common.policies.act.modeling_act import ACTPolicy

cfg = ACTConfig()
policy = ACTPolicy(cfg, dataset_stats=dataset.stats)

# Training loop
for batch in dataloader:
    loss, _ = policy.forward(batch)
    loss.backward()
    optimizer.step()
```

## Configuration Reference

| Platform | Format | Latency | Memory |
|----------|--------|---------|--------|
| Jetson Nano | TensorRT FP16 | 10-30ms | 4GB |
| Jetson Orin | TensorRT FP16 | 2-5ms | 16GB |
| x86 + GPU | TensorRT FP32 | 1-3ms | 24GB+ |
| ARM CPU | ONNX Quantized | 50-100ms | 2GB |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| High latency | Batch size too small | Increase batch, use TensorRT |
| Out of memory | Model too large | Quantize to INT8, prune |
| Accuracy drop | Quantization | Use calibration, partial quantization |

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering TensorRT, ONNX, quantization, Jetson, LeRobot