# Copyright (c) 2021 Oleg Polakow. All rights reserved.
# This code is licensed under Apache 2.0 with Commons Clause license (see LICENSE.md for details)

"""Class and function decorators."""

from vectorbt import _typing as tp
from vectorbt.utils import checks
from vectorbt.utils.config import Config
from vectorbt.utils.decorators import cached_method
from vectorbt.utils.parsing import get_func_arg_names

WrapperFuncT = tp.Callable[[tp.Type[tp.T]], tp.Type[tp.T]]


def attach_returns_acc_methods(config: Config) -> WrapperFuncT:
    """Class decorator to add returns accessor methods.

    `config` must contain target method names (keys) and dictionaries (values) with the following keys:

    * `source_name`: Name of the source method. Defaults to the target name.
    * `docstring`: Method docstring. Defaults to "See `vectorbt.returns.accessors.ReturnsAccessor.{source_name}`.".

    The class must be a subclass of `vectorbt.portfolio.base.Portfolio`.
    """

    def wrapper(cls: tp.Type[tp.T]) -> tp.Type[tp.T]:
        checks.assert_subclass_of(cls, "Portfolio")

        for target_name, settings in config.items():
            source_name = settings.get('source_name', target_name)
            docstring = settings.get('docstring', f"See `vectorbt.returns.accessors.ReturnsAccessor.{source_name}`.")

            def new_method(self,
                           *,
                           group_by: tp.GroupByLike = None,
                           benchmark_rets: tp.Optional[tp.ArrayLike] = None,
                           freq: tp.Optional[tp.FrequencyLike] = None,
                           year_freq: tp.Optional[tp.FrequencyLike] = None,
                           use_asset_returns: bool = False,
                           jitted: tp.JittedOption = None,
                           _source_name: str = source_name,
                           **kwargs) -> tp.Any:
                returns_acc = self.get_returns_acc(
                    group_by=group_by,
                    benchmark_rets=benchmark_rets,
                    freq=freq,
                    year_freq=year_freq,
                    use_asset_returns=use_asset_returns,
                    jitted=jitted
                )
                ret_method = getattr(returns_acc, _source_name)
                if 'jitted' in get_func_arg_names(ret_method):
                    kwargs['jitted'] = jitted
                return ret_method(**kwargs)

            new_method.__name__ = 'get_' + target_name
            new_method.__qualname__ = f"{cls.__name__}.get_{target_name}"
            new_method.__doc__ = docstring
            setattr(cls, new_method.__name__, new_method)

            def new_prop(self, _target_name: str = target_name) -> tp.Any:
                return getattr(self, 'get_' + _target_name)()

            new_prop.__name__ = target_name
            new_prop.__qualname__ = f"{cls.__name__}.{target_name}"
            new_prop.__doc__ = f"`{cls.__name__}.get_{target_name}` with default arguments."
            setattr(cls, new_prop.__name__, property(new_prop))
        return cls

    return wrapper
