from bson.codec_options import TypeRegistry

from app.db.codecs import decimal_codec

type_registry = TypeRegistry([decimal_codec])
