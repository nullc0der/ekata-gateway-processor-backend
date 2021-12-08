from decimal import Decimal
from bson.decimal128 import Decimal128
from bson.codec_options import TypeCodec


class DecimalCodec(TypeCodec):
    python_type = Decimal
    bson_type = Decimal128

    def transform_python(self, value: Decimal) -> Decimal128:
        return Decimal128(value)

    def transform_bson(self, value: Decimal128) -> Decimal:
        return value.to_decimal()


decimal_codec = DecimalCodec()
