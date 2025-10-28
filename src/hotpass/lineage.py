"""Helpers for emitting OpenLineage events from Hotpass runs."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from uuid import uuid4

try:
    from openlineage.client import OpenLineageClient
    from openlineage.client import set_producer as set_lineage_producer
    from openlineage.client.event_v2 import (
        InputDataset,
        Job,
        OutputDataset,
        Run,
        RunEvent,
        RunState,
    )
except Exception:  # pragma: no cover - optional dependency
    OpenLineageClient = None  # type: ignore[assignment]
    set_lineage_producer = None  # type: ignore[assignment]
    InputDataset = OutputDataset = Job = Run = RunEvent = RunState = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DEFAULT_NAMESPACE = "hotpass.local"
DEFAULT_PRODUCER = "https://hotpass.dev/lineage"

DatasetSpec = str | Path | Mapping[str, object]


class LineageEmitter:
    """Thin wrapper around the OpenLineage client with graceful fallbacks."""

    def __init__(
        self,
        job_name: str,
        *,
        run_id: str | None = None,
        namespace: str | None = None,
        producer: str | None = None,
    ) -> None:
        self.job_name = job_name
        self.namespace = namespace or os.getenv("HOTPASS_LINEAGE_NAMESPACE", DEFAULT_NAMESPACE)
        self.run_id = str(run_id or uuid4())
        self.producer = producer or os.getenv("HOTPASS_LINEAGE_PRODUCER", DEFAULT_PRODUCER)
        self._inputs: Sequence[InputDataset] | None = None  # type: ignore[assignment]

        self._client = self._initialise_client()
        self._active = self._client is not None
        if self._active and set_lineage_producer is not None:
            try:
                set_lineage_producer(self.producer)
            except Exception:  # pragma: no cover - defensive guard
                logger.debug("Unable to set OpenLineage producer URI", exc_info=True)

    @property
    def is_enabled(self) -> bool:
        return self._active

    def emit_start(
        self,
        *,
        inputs: Iterable[DatasetSpec] | None = None,
    ) -> None:
        if not self._active:
            return
        self._inputs = self._build_datasets(inputs or (), InputDataset)
        event = RunEvent(
            eventTime=_now(),
            producer=self.producer,
            eventType=RunState.START,
            run=Run(runId=self.run_id),
            job=Job(namespace=self.namespace, name=self.job_name),
            inputs=list(self._inputs),
            outputs=[],
        )
        self._emit(event)

    def emit_complete(
        self,
        *,
        outputs: Iterable[DatasetSpec] | None = None,
    ) -> None:
        if not self._active:
            return
        event = RunEvent(
            eventTime=_now(),
            producer=self.producer,
            eventType=RunState.COMPLETE,
            run=Run(runId=self.run_id),
            job=Job(namespace=self.namespace, name=self.job_name),
            inputs=list(self._inputs or []),
            outputs=self._build_datasets(outputs or (), OutputDataset),
        )
        self._emit(event)

    def emit_fail(
        self,
        message: str,
        *,
        outputs: Iterable[DatasetSpec] | None = None,
    ) -> None:
        if not self._active:
            return
        event = RunEvent(
            eventTime=_now(),
            producer=self.producer,
            eventType=RunState.FAIL,
            run=Run(runId=self.run_id),
            job=Job(namespace=self.namespace, name=self.job_name),
            inputs=list(self._inputs or []),
            outputs=self._build_datasets(outputs or (), OutputDataset),
        )
        logger.debug("Emitting OpenLineage FAIL event for %s: %s", self.job_name, message)
        self._emit(event)

    def _initialise_client(self) -> OpenLineageClient | None:
        if OpenLineageClient is None:
            return None
        if os.getenv("HOTPASS_DISABLE_LINEAGE", "0") == "1":
            return None
        try:
            return OpenLineageClient()
        except Exception:  # pragma: no cover - defensive guard
            logger.warning("OpenLineage client unavailable", exc_info=True)
            return None

    def _emit(self, event: RunEvent) -> None:  # type: ignore[valid-type]
        if not self._active or self._client is None:
            return
        try:
            self._client.emit(event)
        except Exception:  # pragma: no cover - defensive guard
            logger.warning("Failed to emit OpenLineage event", exc_info=True)

    def _build_datasets(
        self,
        specs: Iterable[DatasetSpec],
        dataset_cls: type[InputDataset] | type[OutputDataset],  # type: ignore[valid-type]
    ) -> list[InputDataset] | list[OutputDataset]:  # type: ignore[valid-type]
        datasets: list[InputDataset] | list[OutputDataset] = []
        for spec in specs:
            dataset = self._normalise_dataset(spec, dataset_cls)
            if dataset is not None:
                datasets.append(dataset)
        return datasets

    def _normalise_dataset(
        self,
        spec: DatasetSpec,
        dataset_cls: type[InputDataset] | type[OutputDataset],  # type: ignore[valid-type]
    ) -> InputDataset | OutputDataset | None:  # type: ignore[valid-type]
        namespace = self.namespace
        facets: Mapping[str, object] | None = None
        name: str | None = None

        try:
            if isinstance(spec, Mapping):
                name = str(spec.get("name") or "").strip() or None
                namespace = str(spec.get("namespace") or namespace)
                facets = spec.get("facets")  # type: ignore[assignment]
            elif isinstance(spec, Path):
                name = str(spec.expanduser().resolve())
            else:
                candidate = str(spec).strip()
                if candidate:
                    name = _normalise_path_string(candidate)
        except Exception:  # pragma: no cover - defensive guard
            logger.debug(
                "Unable to convert dataset spec '%s' into OpenLineage dataset",
                spec,
                exc_info=True,
            )
            return None

        if not name:
            return None
        try:
            return dataset_cls(namespace=namespace, name=name, facets=facets or {})
        except Exception:  # pragma: no cover - defensive guard
            logger.debug(
                "Failed to instantiate %s for %s",
                dataset_cls.__name__,
                name,
                exc_info=True,
            )
        return None


class NullLineageEmitter(LineageEmitter):
    """No-op variant used when OpenLineage is unavailable."""

    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        self.job_name = ""
        self.namespace = DEFAULT_NAMESPACE
        self.run_id = str(uuid4())
        self.producer = DEFAULT_PRODUCER
        self._inputs = None
        self._client = None
        self._active = False

    def emit_start(self, *, inputs: Iterable[DatasetSpec] | None = None) -> None:  # noqa: D401, ARG002
        return

    def emit_complete(
        self,
        *,
        outputs: Iterable[DatasetSpec] | None = None,  # noqa: D401, ARG002
    ) -> None:
        return

    def emit_fail(
        self,
        message: str,  # noqa: D401, ARG002
        *,
        outputs: Iterable[DatasetSpec] | None = None,  # noqa: ARG002
    ) -> None:
        return


def create_emitter(
    job_name: str,
    *,
    run_id: str | None = None,
    namespace: str | None = None,
    producer: str | None = None,
) -> LineageEmitter:
    emitter = LineageEmitter(
        job_name,
        run_id=run_id,
        namespace=namespace,
        producer=producer,
    )
    if emitter.is_enabled:
        return emitter
    return NullLineageEmitter()


def _now() -> str:
    return datetime.now(datetime.UTC).isoformat()


def _normalise_path_string(value: str) -> str:
    if "://" in value:
        return value
    return str(Path(value).expanduser())


__all__ = ["create_emitter", "LineageEmitter", "NullLineageEmitter"]
