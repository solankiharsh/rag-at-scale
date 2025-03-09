import asyncio

from confluent_kafka import KafkaError, Message, Producer
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor

from config import Config
from utils.platform_commons.logger import logger

settings = Config()

# Instrument kafka
instrumentation = ConfluentKafkaInstrumentor()

# Singleton Kafka producer
_kafka_producer = None


def create_kafka_producer(bootstrap_servers: str) -> Producer:
    producer = Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "queue.buffering.max.messages": 10000000,  # 10M messages
            "security.protocol": "SSL",
            "ssl.ca.location": settings.kafka_ca_location,
            "ssl.certificate.location": settings.kafka_certificate_location,
            "ssl.key.location": settings.kafka_key_location,
            # Disable hostname verification because configured broker hostname & DNS will not match.
            "ssl.endpoint.identification.algorithm": "none",
        }
    )
    producer = instrumentation.instrument_producer(producer)

    return producer


def uh_delivery_report(err: KafkaError | None, msg: Message):
    """Logs the result of an attempt to deliver a usage history message via Kafka.

    This callback function is intended for use with Kafka's asynchronous message delivery. It logs
    whether the delivery succeeded or failed.

    Args:
        err (confluent_kafka.KafkaError): Error information if the delivery failed, or None if
        the delivery was successful.
        msg (confluent_kafka.Message): The message object, providing access to message details for
        logging purposes.

    """

    if err is not None:
        error_msg = err or "KafkaError"

        logger.error(
            f"Usage History event delivery failed: {error_msg}",
            exception=Exception(error_msg),
        )
    else:
        pass


async def poll_delivery_notifications(producer: Producer):
    """Regularly polls Kafka producer for delivery notifications.

    This function is designed to run as an infinite loop in a background task. It frequently
    polls the Kafka producer for delivery report callbacks. To prevent blocking the event loop
    excessively, it polls with a minimal timeout and then waits asynchronously before polling again.

    Args:
        producer (confluent_kafka.Producer): The Kafka producer instance used for message
        production.

    """

    while True:
        producer.poll(0.01)  # this blocks the event loop and needs to be minimal
        await asyncio.sleep(5)  # we don't need to be doing this that often, wait between


def get_kafka_producer() -> Producer:
    global _kafka_producer
    if _kafka_producer is None:
        logger.info("Kafka producer initialized for usage history events.")
        _kafka_producer = create_kafka_producer(settings.kafka_usage_history_brokers)
        asyncio.create_task(poll_delivery_notifications(_kafka_producer))
    return _kafka_producer
