import logging
import time

import cv2
from onnx_ocr import ONNXPaddleOcr

from utils.elapsed import timeit
from utils.helper import process_bounding_box
from utils.logger import get_logger

logger = get_logger(__name__, logging.DEBUG)


@timeit
def test_rec(fp: str = "./images/shijuan.jpg"):
    model = ONNXPaddleOcr(
        use_angle_cls=False,
        use_gpu=False,
        cpu_threads=16,  # CPU推理线程数
        det_model_dir="",
        rec_model_dir="",
    )
    img = cv2.imread(fp)
    s = time.time()
    result = model.ocr(img)
    e = time.time()
    logger.debug("total time: {:.3f}".format(e - s))
    ocr_results = [
        {
            "text": line[1][0],
            "confidence": float(line[1][1]),
            "bounding_box": process_bounding_box(line[0]),
        }
        for line in result[0]
    ]

    texts = [item["text"] for item in ocr_results]
    logger.debug(texts)
    logger.debug(ocr_results)

    # 保存结果到图像和JSON文件
    # save_to_img(img, result, "./output")
    # save_to_json(ocr_results, "./output")

    # path_obj = Path(fp)
    # out_fp = str(path_obj.with_name(path_obj.stem + "_rec" + path_obj.suffix))

    # sav2Img(img, result, out_fp)


if __name__ == "__main__":
    # test_rec("./images/27_crop.jpg")
    test_rec("./images/test.jpg")

    # path_obj = Path("./images/shijuan.jpg")
    # output_base = Path("./output")
    # out_fp = str(output_base / f"{path_obj.stem}_rec.json")
    # out_fp = str(path_obj.with_name(path_obj.stem + "_rec.json"))
    # logger.debug(out_fp)
