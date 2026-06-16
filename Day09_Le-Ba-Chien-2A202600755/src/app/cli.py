from __future__ import annotations

import argparse
from pathlib import Path

from app.graph import ShoppingAssistant


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student scaffold CLI.")
    parser.add_argument("--question", help="Run one question through the graph.")
    parser.add_argument("--test-file", default="data/test.json")
    parser.add_argument("--trace-file", default=None)
    parser.add_argument("--batch", action="store_true")
    return parser


def main() -> None:
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    args = build_parser().parse_args()
    assistant = ShoppingAssistant()

    if args.batch:
        print(f"Chạy batch testing với file: {args.test_file}...")
        # Đảm bảo output directory tồn tại
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        summary = assistant.run_batch(
            test_file=Path(args.test_file),
            output_dir=output_dir,
            rebuild_index=True # Rebuild cho lần chạy đầu
        )
        print("\nHoàn tất chạy batch!")
        print(f"Tổng số test: {summary['total']}")
        print(f"Thành công: {summary['passed']}")
        print(f"Summary được lưu tại: {output_dir / 'summary.json'}")
    elif args.question:
        print(f"Hỏi: {args.question}")
        res = assistant.ask(
            question=args.question,
            trace_file=Path(args.trace_file) if args.trace_file else None,
            rebuild_index=False
        )
        print("\n---\nCâu trả lời:")
        print(res.get("final_answer", "Không có câu trả lời."))
    else:
        print("Vui lòng truyền thêm cờ --question <câu hỏi> hoặc --batch để chạy.")


if __name__ == "__main__":
    main()
