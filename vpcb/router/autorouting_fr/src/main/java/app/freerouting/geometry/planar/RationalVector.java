package app.freerouting.geometry.planar;

import app.freerouting.datastructures.BigIntAux;
import app.freerouting.datastructures.Signum;

import java.io.Serializable;
import java.math.BigInteger;

/**
 * Analog RationalPoint, but implementing the functionality of a Vector instead of the functionality
 * of a Point.
 */
public class RationalVector extends Vector implements Serializable {
  public final BigInteger x;
  public final BigInteger y;
  public final BigInteger z;

  /**
   * creates a RationalVector from 3 BigIntegers p_x, p_y and p_z. They represent the 2-dimensional
   * Vector with the rational number Tuple ( p_x / p_z , p_y / p_z).
   */
  public RationalVector(BigInteger p_x, BigInteger p_y, BigInteger p_z) {
    if (p_z.signum() >= 0) {
      x = p_x;
      y = p_y;
      z = p_z;

    } else {
      x = p_x.negate();
      y = p_y.negate();
      z = p_z.negate();
    }
  }

  /** creates a RationalVector from an IntVector */
  RationalVector(IntVector p_vector) {
    x = BigInteger.valueOf(p_vector.x);
    y = BigInteger.valueOf(p_vector.y);
    z = BigInteger.ONE;
  }

  /** returns true, if the x and y coordinates of this vector are 0 */
  @Override
  public final boolean is_zero() {
    return x.signum() == 0 && y.signum() == 0;
  }

  /** returns true, if this RationalVector is equal to p_ob */
  @Override
  public final boolean equals(Object p_ob) {
    if (this == p_ob) {
      return true;
    }
    if (p_ob == null) {
      return false;
    }
    if (getClass() != p_ob.getClass()) {
      return false;
    }
    RationalPoint other = (RationalPoint) p_ob;
    BigInteger det = BigIntAux.determinant(x, other.x, z, other.z);
    if (det.signum() != 0) {
      return false;
    }
    det = BigIntAux.determinant(y, other.y, z, other.z);

    return (det.signum() == 0);
  }

  /** returns the Vector such that this plus this.minus() is zero */
  @Override
  public Vector negate() {
    return new RationalVector(x.negate(), y.negate(), z);
  }

  /** adds p_other to this vector */
  @Override
  public final Vector add(Vector p_other) {
    return p_other.add(this);
  }

  /**
   * Let L be the line from the Zero Vector to p_other. The function returns Side.ON_THE_LEFT, if
   * this Vector is on the left of L Side.ON_THE_RIGHT, if this Vector is on the right of L and
   * Side.COLLINEAR, if this Vector is collinear with L.
   */
  @Override
  public Side side_of(Vector p_other) {
    Side tmp = p_other.side_of(this);
    return tmp.negate();
  }

  @Override
  public boolean is_orthogonal() {
    return (x.signum() == 0 || y.signum() == 0);
  }

  @Override
  public boolean is_diagonal() {
    return x.abs().equals(y.abs());
  }

  /**
   * The function returns Signum.POSITIVE, if the scalar product of this vector and p_other
   * {@literal >} 0, Signum.NEGATIVE, if the scalar product is {@literal <} 0, and Signum.ZERO, if
   * the scalar product is equal 0.
   */
  @Override
  public Signum projection(Vector p_other) {
    return p_other.projection(this);
  }

  /** calculates the scalar product of this vector and p_other */
  @Override
  public double scalar_product(Vector p_other) {
    return p_other.scalar_product(this);
  }

  /** approximates the coordinates of this vector by float coordinates */
  @Override
  public FloatPoint to_float() {
    double xd = x.doubleValue();
    double yd = y.doubleValue();
    double zd = z.doubleValue();
    return new FloatPoint(xd / zd, yd / zd);
  }

  @Override
  public Vector change_length_approx(double p_length) {
    System.out.println("RationalVector: change_length_approx not yet implemented");
    return this;
  }

  @Override
  public Vector turn_90_degree(int p_factor) {
    int n = p_factor;
    while (n < 0) {
      n += 4;
    }
    while (n >= 4) {
      n -= 4;
    }
    BigInteger new_x;
    BigInteger new_y;
    switch (n) {
      case 0 -> { // 0 degree
        new_x = x;
        new_y = y;
      }
      case 1 -> { // 90 degree
        new_x = y.negate();
        new_y = x;
      }
      case 2 -> { // 180 degree
        new_x = x.negate();
        new_y = y.negate();
      }
      case 3 -> { // 270 degree
        new_x = y;
        new_y = x.negate();
      }
      default -> {
        return this;
      }
    }
    return new RationalVector(new_x, new_y, this.z);
  }

  @Override
  public Vector mirror_at_y_axis() {
    return new RationalVector(this.x.negate(), this.y, this.z);
  }

  @Override
  public Vector mirror_at_x_axis() {
    return new RationalVector(this.x, this.y.negate(), this.z);
  }

  @Override
  Direction to_normalized_direction() {
    BigInteger dx = x;
    BigInteger dy = y;
    BigInteger gcd = dx.gcd(y);
    dx = dx.divide(gcd);
    dy = dy.divide(gcd);
    if ((dx.abs()).compareTo(Limits.CRIT_INT_BIG) <= 0
        && (dy.abs()).compareTo(Limits.CRIT_INT_BIG) <= 0) {
      return new IntDirection(dx.intValue(), dy.intValue());
    }
    return new BigIntDirection(dx, dy);
  }

  @Override
  double scalar_product(IntVector p_other) {
    Vector other = new RationalVector(p_other);
    return other.scalar_product(this);
  }

  @Override
  double scalar_product(RationalVector p_other) {
    FloatPoint v1 = to_float();
    FloatPoint v2 = p_other.to_float();
    return v1.x * v2.x + v1.y * v2.y;
  }

  @Override
  Signum projection(IntVector p_other) {
    Vector other = new RationalVector(p_other);
    return other.projection(this);
  }

  @Override
  Signum projection(RationalVector p_other) {
    BigInteger tmp1 = x.multiply(p_other.x);
    BigInteger tmp2 = y.multiply(p_other.y);
    BigInteger tmp3 = tmp1.add(tmp2);
    int result = tmp3.signum();
    return Signum.of(result);
  }

  @Override
  final Vector add(IntVector p_other) {
    RationalVector other = new RationalVector(p_other);
    return add(other);
  }

  @Override
  final Vector add(RationalVector p_other) {
    BigInteger[] v1 = new BigInteger[3];
    v1[0] = x;
    v1[1] = y;
    v1[2] = z;

    BigInteger[] v2 = new BigInteger[3];
    v2[0] = p_other.x;
    v2[1] = p_other.y;
    v2[2] = p_other.z;
    BigInteger[] result = BigIntAux.add_rational_coordinates(v1, v2);
    return new RationalVector(result[0], result[1], result[2]);
  }

  @Override
  Point add_to(IntPoint p_point) {
    BigInteger new_x = z.multiply(BigInteger.valueOf(p_point.x));
    new_x = new_x.add(x);
    BigInteger new_y = z.multiply(BigInteger.valueOf(p_point.y));
    new_y = new_y.add(y);
    return new RationalPoint(new_x, new_y, z);
  }

  @Override
  Point add_to(RationalPoint p_point) {
    BigInteger[] v1 = new BigInteger[3];
    v1[0] = x;
    v1[1] = y;
    v1[2] = z;

    BigInteger[] v2 = new BigInteger[3];
    v2[0] = p_point.x;
    v2[1] = p_point.y;
    v2[2] = p_point.z;

    BigInteger[] result = BigIntAux.add_rational_coordinates(v1, v2);
    return new RationalPoint(result[0], result[1], result[2]);
  }

  @Override
  Side side_of(IntVector p_other) {
    RationalVector other = new RationalVector(p_other);
    return side_of(other);
  }

  @Override
  Side side_of(RationalVector p_other) {
    BigInteger tmp_1 = y.multiply(p_other.x);
    BigInteger tmp_2 = x.multiply(p_other.y);
    BigInteger determinant = tmp_1.subtract(tmp_2);
    int signum = determinant.signum();
    return Side.of(signum);
  }
}
