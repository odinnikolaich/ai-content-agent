from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from pipeline.mock_vertical import DEFAULT_TOPIC,run_demo

def main()->int:
    parser=argparse.ArgumentParser(description="Run the free PHASE 2 vertical mock video pipeline")
    parser.add_argument("topic",nargs="?",default=DEFAULT_TOPIC); parser.add_argument("--duration",type=int,default=43,choices=range(43,61)); parser.add_argument("--output-dir",default="output"); args=parser.parse_args()
    result=run_demo(args.topic,args.duration,args.output_dir); print(f"VIDEO_READY={result.resolve()}"); return 0
if __name__=="__main__": raise SystemExit(main())
