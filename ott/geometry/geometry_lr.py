# coding=utf-8
# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""A class describing low-rank geometries."""
import jax
import jax.numpy as jnp
from ott.geometry import geometry


@jax.tree_util.register_pytree_node_class
class LRCGeometry(geometry.Geometry):
  r"""Low-rank Cost Geometry defined by two factors.
  """

  def __init__(self,
               cost_1: jnp.ndarray,
               cost_2: jnp.ndarray,
               **kwargs
               ):
    r"""Initializes a geometry by passing it low-rank factors.

    Args:
      cost_1: jnp.ndarray<float>[num_a, r]
      cost_2: jnp.ndarray<float>[num_b, r]
      **kwargs: additional kwargs to Geometry
    """
    assert cost_1.shape[1] == cost_2.shape[1]
    self.cost_1 = cost_1
    self.cost_2 = cost_2
    self._kwargs = kwargs

    super().__init__(**kwargs)

  @property
  def cost_rank(self):
    return self.cost_1.shape[1]

  @property
  def cost_matrix(self):
    """Returns cost matrix if requested."""
    return jnp.matmul(self.cost_1, self.cost_2.T)

  @property
  def shape(self):
    return (self.cost_1.shape[0], self.cost_2.shape[0])

  @property
  def is_symmetric(self):
    return (self.cost_1.shape[0] == self.cost_2.shape[0] and
            jnp.all(self.cost_1 == self.cost_2))

  def _apply_cost_to_vec(self,
                         vec: jnp.ndarray,
                         axis: int = 0,
                         fn=None) -> jnp.ndarray:
    """Applies [num_a, num_b] fn(cost) (or transpose) to vector.

    Args:
      vec: jnp.ndarray [num_a,] ([num_b,] if axis=1) vector
      axis: axis on which the reduction is done.
      fn: function optionally applied to cost matrix element-wise, before the
        doc product

    Returns:
      A jnp.ndarray corresponding to cost x vector
    """
    if fn is None or geometry.is_linear(fn):
      c1 = self.cost_1 if axis == 1 else self.cost_2
      c2 = self.cost_2 if axis == 1 else self.cost_1
      c2 = fn(c2) if fn is not None else c2
      return jnp.dot(c1, jnp.dot(c2.T, vec))
    # Default to super class application and instantiation of cost matrix
    return super()._apply_cost_to_vec(vec, axis, fn)

  def tree_flatten(self):
    return (self.cost_1, self.cost_2, self._kwargs), None

  @classmethod
  def tree_unflatten(cls, aux_data, children):
    del aux_data
    return cls(*children[:-1], **children[-1])


def add_lrc_geom(geom1: LRCGeometry, geom2: LRCGeometry):
  """Add geometry in geom1 to that in geom2, keeping other geom1 params."""
  return LRCGeometry(
      cost_1=jnp.concatenate((geom1.cost_1, geom2.cost_1), axis=1),
      cost_2=jnp.concatenate((geom1.cost_2, geom2.cost_2), axis=1),
      **geom1._kwargs)
